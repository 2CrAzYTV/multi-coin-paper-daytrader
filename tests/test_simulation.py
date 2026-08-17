import tempfile
import unittest
from pathlib import Path

from app.backtest import Backtester
from app.config import Settings
from app.db import Repository
from app.engine import PaperEngine
from app.market_data import MarketData
from app.models import BITPANDA_PAPER_LEVERAGES, STRATEGIES


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(
            data_source="demo",
            data_dir=Path(self.temp_dir.name),
            history_bars=180,
            backtest_bars=400,
            starting_capital=1_000,
            risk_per_trade=0.005,
            max_aggregate_risk=0.01,
            max_daily_loss=0.02,
        )
        self.settings.validate()
        self.market = MarketData(self.settings)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_universe_contains_five_eur_crypto_pairs(self):
        self.assertEqual(
            self.settings.pairs,
            ("BTC-EUR", "ETH-EUR", "SOL-EUR", "XRP-EUR", "ADA-EUR"),
        )
        self.assertTrue(all(pair.endswith("-EUR") for pair in self.settings.pairs))
        self.assertNotIn("XAU-EUR", self.settings.pairs)

    def test_bitpanda_paper_leverage_presets_are_available(self):
        self.assertEqual(BITPANDA_PAPER_LEVERAGES, (1.0, 2.0, 3.0, 5.0, 10.0))
        long_short = [strategy for strategy in STRATEGIES if strategy.short_allowed]
        self.assertEqual(
            tuple(strategy.max_leverage for strategy in long_short),
            BITPANDA_PAPER_LEVERAGES,
        )
        self.assertEqual(len(STRATEGIES), 6)

    def test_demo_source_returns_distinct_ohlcv_for_each_pair(self):
        closes = []
        for pair in self.settings.pairs:
            frame = self.market.history(pair, "15m", 120)
            self.assertEqual(list(frame.columns), ["Open", "High", "Low", "Close", "Volume"])
            self.assertGreaterEqual(len(frame), 120)
            closes.append(round(float(frame.iloc[-1]["Close"]), 6))
        self.assertEqual(len(set(closes)), len(self.settings.pairs))

    def test_backtest_runs_shared_portfolio_for_all_strategies(self):
        result = Backtester(self.settings, self.market).run(400)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["pairs"], sorted(self.settings.pairs))
        self.assertEqual(len(result["strategies"]), 6)
        for strategy in result["strategies"]:
            self.assertGreater(strategy["final_equity"], 0)
            self.assertLessEqual(strategy["max_positions"], 2)
            self.assertLessEqual(strategy["max_drawdown_pct"], 10.1)
            self.assertTrue(strategy["curve"])

    def test_paper_cycle_is_idempotent_per_closed_candle(self):
        repository = Repository(self.settings.database_path, 1_000)
        repository.initialize()
        engine = PaperEngine(self.settings, repository, self.market)
        first = engine.run_once()
        second = engine.run_once()
        self.assertEqual(first["status"], "ok")
        self.assertEqual(second["status"], "no_new_candles")
        self.assertEqual(len(repository.list_markets()), 5)
        self.assertEqual(len(engine.serialize_portfolios()), 6)

    def test_every_open_position_has_stop_target_and_global_count_cap(self):
        repository = Repository(self.settings.database_path, 1_000)
        repository.initialize()
        engine = PaperEngine(self.settings, repository, self.market)
        engine.run_once()
        for portfolio in repository.list_portfolios():
            positions = repository.list_positions(portfolio["strategy_id"])
            self.assertLessEqual(len(positions), self.settings.max_open_positions)
            self.assertLessEqual(
                sum(float(position["initial_risk"]) for position in positions),
                10.01,
            )
            for position in positions:
                self.assertGreater(position["stop_price"], 0)
                self.assertGreater(position["take_profit"], 0)

    def test_market_client_has_no_order_or_transfer_methods(self):
        public_methods = {
            name for name in dir(self.market) if not name.startswith("_")
        }
        self.assertFalse(public_methods & {"order", "create_order", "cancel_order", "transfer"})


if __name__ == "__main__":
    unittest.main()
