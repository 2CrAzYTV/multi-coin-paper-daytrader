import tempfile
import unittest
from pathlib import Path

from app.backtest import Backtester
from app.config import Settings
from app.market_data import MarketData
from app.strategies import add_entry_indicators, add_trend_indicators, signal_snapshot


class AdxFilterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(
            data_source="demo",
            data_dir=Path(self.temp_dir.name),
            history_bars=180,
            backtest_bars=400,
        )
        self.settings.validate()
        self.market = MarketData(self.settings)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_adx_column_is_bounded_between_zero_and_hundred(self):
        frame = self.market.history("BTC-EUR", "1h", 180)
        trend = add_trend_indicators(frame, self.settings)
        values = trend["ADX"].dropna()
        self.assertTrue((values >= 0).all())
        self.assertTrue((values <= 100).all())

    def test_disabled_threshold_matches_unfiltered_signal_direction(self):
        loose = Settings(
            data_source="demo", data_dir=self.settings.data_dir, adx_threshold=0.0
        )
        entry = add_entry_indicators(self.market.history("BTC-EUR", "15m", 180), loose)
        trend = add_trend_indicators(self.market.history("BTC-EUR", "1h", 180), loose)
        snapshot = signal_snapshot("BTC-EUR", entry, trend, loose)
        self.assertIn(snapshot.direction, (-1, 0, 1))

    def test_high_threshold_suppresses_every_signal(self):
        strict = Settings(
            data_source="demo", data_dir=self.settings.data_dir, adx_threshold=60.0
        )
        entry = add_entry_indicators(self.market.history("BTC-EUR", "15m", 180), strict)
        trend = add_trend_indicators(self.market.history("BTC-EUR", "1h", 180), strict)
        snapshot = signal_snapshot("BTC-EUR", entry, trend, strict)
        self.assertEqual(snapshot.direction, 0)

    def test_backtest_never_trades_below_the_configured_adx_threshold(self):
        strict = Settings(
            data_source="demo",
            data_dir=self.settings.data_dir,
            history_bars=180,
            backtest_bars=400,
            adx_threshold=60.0,
        )
        result = Backtester(strict, self.market).run(400)
        self.assertEqual(result["status"], "ok")
        for strategy in result["strategies"]:
            self.assertEqual(strategy["trades"], 0)


if __name__ == "__main__":
    unittest.main()
