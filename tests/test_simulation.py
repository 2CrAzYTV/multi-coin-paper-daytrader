import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from app.backtest import Backtester
from app.config import Settings
from app.db import Repository
from app.engine import PaperEngine
from app.market_data import MarketData
from app.models import STRATEGY, SignalSnapshot


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(data_source="demo", data_dir=Path(self.temp_dir.name), starting_capital=1_000)
        self.settings.validate()
        self.market = MarketData(self.settings)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _engine(self):
        repository = Repository(self.settings.database_path, self.settings.starting_capital)
        repository.initialize()
        return repository, PaperEngine(self.settings, repository, self.market)

    def test_default_universe_is_the_four_most_liquid_fusion_pairs(self):
        self.assertEqual(self.settings.pairs, ("BTC-EUR", "ETH-EUR", "SOL-EUR", "XRP-EUR"))
        self.assertEqual(self.settings.candle_interval, "1d")

    def test_backtest_is_long_only_spot_with_fees(self):
        result = Backtester(self.settings, self.market).run(1_440)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["strategies"]), 1)
        strategy = result["strategies"][0]
        self.assertGreater(strategy["final_equity"], 0)
        self.assertLessEqual(strategy["max_positions"], self.settings.max_open_positions)
        self.assertGreater(strategy["trades"], 0)
        self.assertGreater(strategy["fees_paid"], 0)
        self.assertTrue(strategy["curve"])
        for point in strategy["curve"]:
            self.assertGreaterEqual(point["equity"], 0)

    def test_paper_cycle_is_idempotent_per_closed_candle(self):
        repository, engine = self._engine()
        self.assertEqual(engine.run_once()["status"], "ok")
        self.assertEqual(engine.run_once()["status"], "no_new_candles")
        self.assertEqual(len(repository.list_markets()), 4)
        self.assertEqual(len(engine.serialize_portfolios()), 1)

    def _snapshot(self, pair, direction, price=100.0):
        return SignalSnapshot(pair, datetime.now(UTC).isoformat(), price, 2.0, 99.0, 90.0, direction, 1.0, "test")

    def test_buy_and_sell_charge_fees_and_never_spend_more_than_cash(self):
        repository, engine = self._engine()
        constraints = self.market.pair_constraints()
        now = datetime.now(UTC)
        snapshots = {pair: self._snapshot(pair, 1) for pair in self.settings.pairs}
        engine._process(snapshots, constraints, set(snapshots), now)
        portfolio = repository.get_portfolio(STRATEGY.strategy_id)
        positions = repository.list_positions(STRATEGY.strategy_id)
        self.assertEqual(len(positions), 4)
        self.assertGreaterEqual(engine.cash(portfolio, positions), -1e-6)
        self.assertGreater(portfolio["fees_paid"], 0)
        # flat price round trip loses exactly fees + slippage
        snapshots = {pair: self._snapshot(pair, -1) for pair in self.settings.pairs}
        engine._process(snapshots, constraints, set(snapshots), now)
        portfolio = repository.get_portfolio(STRATEGY.strategy_id)
        self.assertEqual(repository.list_positions(STRATEGY.strategy_id), [])
        cost = 1_000 - portfolio["realized_balance"]
        self.assertGreater(cost, 1_000 * 2 * self.settings.fee_rate * 0.95)
        self.assertLess(cost, 1_000 * 2 * (self.settings.fee_rate + self.settings.slippage_rate) * 1.05)

    def test_old_intraday_tables_are_left_untouched(self):
        repository, _ = self._engine()
        import sqlite3
        connection = sqlite3.connect(self.settings.database_path)
        connection.execute("CREATE TABLE dt_portfolios (strategy_id TEXT)")
        connection.execute("INSERT INTO dt_portfolios VALUES ('long_short_2x')")
        connection.commit()
        connection.close()
        repository.reset()
        connection = sqlite3.connect(self.settings.database_path)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM dt_portfolios").fetchone()[0], 1)
        connection.close()

    def test_market_client_has_no_order_or_transfer_methods(self):
        public_methods = {name for name in dir(self.market) if not name.startswith("_")}
        self.assertFalse(public_methods & {"order", "create_order", "cancel_order", "transfer"})


if __name__ == "__main__":
    unittest.main()
