import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.backtest import Backtester
from app.config import Settings
from app.db import Repository
from app.engine import PaperEngine
from app.market_data import MarketData
from app.models import STRATEGY
from app.tax import is_taxable, settle_year


class TaxRuleTests(unittest.TestCase):
    def test_holding_period(self):
        self.assertTrue(is_taxable(365))
        self.assertFalse(is_taxable(365.5))

    def test_freigrenze_is_not_a_freibetrag(self):
        below = settle_year([999.99], loss_carryforward=0, rate=0.3, allowance=1_000)
        self.assertEqual(below.tax, 0.0)
        at = settle_year([1_000.0], loss_carryforward=0, rate=0.3, allowance=1_000)
        self.assertEqual(at.tax, 300.0)  # the whole amount, not only the excess

    def test_losses_offset_gains_and_carry_forward(self):
        year1 = settle_year([500, -2_000], loss_carryforward=0, rate=0.3, allowance=1_000)
        self.assertEqual(year1.tax, 0.0)
        self.assertEqual(year1.loss_carryforward, 1_500)
        # below the Freigrenze the carryforward is not consumed
        year2 = settle_year([800], loss_carryforward=1_500, rate=0.3, allowance=1_000)
        self.assertEqual((year2.tax, year2.loss_carryforward), (0.0, 1_500))
        year3 = settle_year([2_000], loss_carryforward=1_500, rate=0.3, allowance=1_000)
        self.assertEqual((year3.tax, year3.loss_carryforward), (150.0, 0.0))


class EngineTaxTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(data_source="demo", data_dir=Path(self.temp_dir.name), starting_capital=10_000)
        self.repository = Repository(self.settings.database_path, 10_000)
        self.repository.initialize()
        self.engine = PaperEngine(self.settings, self.repository, MarketData(self.settings))

    def tearDown(self):
        self.temp_dir.cleanup()

    def _closed(self, pnl, days, closed_at):
        trade_id = self.repository.open_trade(
            strategy_id=STRATEGY.strategy_id, pair="BTC-EUR", opened_at=(closed_at - timedelta(days=days)).isoformat(),
            units=1, entry_price=1_000, entry_fee=0, fill_source="candle",
        )
        self.repository.close_trade(
            trade_id=trade_id, closed_at=closed_at.isoformat(), exit_price=1_000 + pnl, exit_fee=0,
            fill_source="candle", pnl=pnl, pnl_pct=pnl / 1_000, holding_days=days,
            taxable=is_taxable(days), reason="test",
        )

    def test_year_change_pays_tax_once_and_ignores_long_holdings(self):
        portfolio = self.repository.get_portfolio(STRATEGY.strategy_id)
        self.engine._settle_taxes(portfolio, datetime(2026, 6, 1, tzinfo=UTC))
        self.assertEqual(portfolio["tax_year"], 2026)
        self._closed(2_000, 30, datetime(2026, 7, 1, tzinfo=UTC))
        self._closed(5_000, 400, datetime(2026, 8, 1, tzinfo=UTC))  # tax-free
        self.repository.save_portfolio(portfolio)
        status = self.engine.serialize_portfolios()[0]
        self.assertEqual(status["tax_estimate_year"], 600.0)
        balance = float(portfolio["realized_balance"])
        self.engine._settle_taxes(portfolio, datetime(2027, 1, 2, tzinfo=UTC))
        self.assertAlmostEqual(float(portfolio["realized_balance"]), balance - 600.0)
        self.assertEqual(portfolio["tax_year"], 2027)
        self.engine._settle_taxes(portfolio, datetime(2027, 3, 1, tzinfo=UTC))
        self.assertAlmostEqual(float(portfolio["realized_balance"]), balance - 600.0)

    def test_existing_v030_database_gets_tax_columns(self):
        path = Path(self.temp_dir.name) / "old.sqlite3"
        connection = sqlite3.connect(path)
        connection.execute(
            "CREATE TABLE tf_portfolios (strategy_id TEXT PRIMARY KEY, label TEXT NOT NULL, "
            "starting_capital REAL NOT NULL, realized_balance REAL NOT NULL, peak_equity REAL NOT NULL, "
            "fees_paid REAL NOT NULL DEFAULT 0, last_run_at TEXT, updated_at TEXT NOT NULL)"
        )
        connection.commit()
        connection.close()
        Repository(path, 100).initialize()
        connection = sqlite3.connect(path)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(tf_portfolios)")}
        connection.close()
        self.assertTrue({"tax_year", "tax_paid", "loss_carryforward"} <= columns)

    def test_backtest_reports_pre_and_after_tax(self):
        result = Backtester(self.settings, MarketData(self.settings)).run(1_440)
        strategy = result["strategies"][0]
        self.assertIn("taxes_paid", strategy)
        self.assertGreaterEqual(strategy["pre_tax_final_equity"], strategy["final_equity"])
        self.assertEqual(result["benchmark"]["taxes_paid"], 0.0)  # held > 1 year


if __name__ == "__main__":
    unittest.main()
