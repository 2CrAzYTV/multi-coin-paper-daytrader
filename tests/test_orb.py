import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.backtest import Backtester
from app.config import Settings
from app.market_data import MarketData
from app.strategies import add_entry_indicators, add_orb_columns


def _frame(closes, start="2026-11-02 12:00", tz="Europe/Berlin"):
    """15m candles (index = open time) with a tight 1-unit wick around each close."""
    index = pd.date_range(start=start, periods=len(closes), freq="15min", tz=tz).tz_convert("UTC")
    close = pd.Series(closes, index=index, dtype=float)
    return pd.DataFrame(
        {
            "Open": close.shift(1).fillna(close.iloc[0]),
            "High": close + 0.5,
            "Low": close - 0.5,
            "Close": close,
            "Volume": 1_000.0,
        },
        index=index,
    )


class OrbTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(
            data_source="demo",
            data_dir=Path(self.temp_dir.name),
            history_bars=180,
            backtest_bars=400,
            orb_trend_filter=False,
        )
        self.settings.validate()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _signals(self, closes, settings=None):
        settings = settings or self.settings
        data = add_entry_indicators(_frame(closes), settings)
        return add_orb_columns(data, settings).tz_convert("Europe/Berlin")

    def test_first_close_above_range_is_the_only_long_signal(self):
        # 12:00-15:15 flat at 100 (14 candles), range 15:30+15:45 = 100/101,
        # then breakout at 16:00 (103) and a second higher close at 16:15.
        closes = [100.0] * 14 + [100.0, 101.0, 103.0, 104.0, 102.0]
        data = self._signals(closes)
        signals = data[data["ORB_SIGNAL"] != 0]
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals.index[0].strftime("%H:%M"), "16:00")
        self.assertEqual(int(signals.iloc[0]["ORB_SIGNAL"]), 1)
        self.assertAlmostEqual(float(signals.iloc[0]["ORB_HIGH"]), 101.5)
        self.assertAlmostEqual(float(signals.iloc[0]["ORB_LOW"]), 99.5)
        # stop distance = close - range midpoint (100.5)
        self.assertAlmostEqual(float(signals.iloc[0]["ORB_STOP"]), 2.5)
        self.assertEqual(data.loc[data.index[17], "ORB_REASON"], "ORB breakout already used today")

    def test_no_signal_inside_the_range_or_after_the_window(self):
        short_window = Settings(
            data_source="demo",
            data_dir=self.settings.data_dir,
            orb_trend_filter=False,
            orb_entry_window_minutes=15,
        )
        closes = [100.0] * 14 + [100.0, 101.0, 101.0, 105.0]
        data = self._signals(closes, short_window)
        self.assertEqual(int((data["ORB_SIGNAL"] != 0).sum()), 0)
        self.assertEqual(data.iloc[14]["ORB_REASON"], "Building the ORB opening range")
        self.assertEqual(data.iloc[-1]["ORB_REASON"], "Outside the ORB entry window")

    def test_short_breakout_below_range(self):
        closes = [100.0] * 14 + [100.0, 101.0, 97.0]
        data = self._signals(closes)
        self.assertEqual(int(data.iloc[-1]["ORB_SIGNAL"]), -1)

    def test_too_wide_range_is_skipped(self):
        strict = Settings(
            data_source="demo",
            data_dir=self.settings.data_dir,
            orb_trend_filter=False,
            orb_max_range_atr=0.5,
        )
        closes = [100.0] * 14 + [100.0, 106.0, 110.0]
        data = self._signals(closes, strict)
        self.assertEqual(int(data.iloc[-1]["ORB_SIGNAL"]), 0)
        self.assertEqual(data.iloc[-1]["ORB_REASON"], "ORB range too wide")

    def test_trend_filter_blocks_counter_trend_breakout(self):
        trend = Settings(data_source="demo", data_dir=self.settings.data_dir)
        closes = [100.0] * 14 + [100.0, 101.0, 103.0]
        data = add_entry_indicators(_frame(closes), trend)
        trend_down = pd.Series(False, index=data.index)
        result = add_orb_columns(data, trend, trend_down)
        self.assertEqual(int(result.iloc[-1]["ORB_SIGNAL"]), 0)
        self.assertEqual(result.iloc[-1]["ORB_REASON"], "ORB trend filter")

    def test_invalid_orb_settings_are_rejected(self):
        with self.assertRaises(ValueError):
            Settings(data_source="demo", orb_range_minutes=20).validate()
        with self.assertRaises(ValueError):
            Settings(data_source="demo", orb_session_hour=23, orb_session_minute=30).validate()

    def test_backtest_reports_orb_portfolios(self):
        result = Backtester(self.settings, MarketData(self.settings)).run(400)
        ids = {item["strategy_id"] for item in result["strategies"]}
        self.assertTrue({"orb_long_only_1x", "orb_long_short_1x"} <= ids)
        for item in result["strategies"]:
            self.assertGreater(item["final_equity"], 0)


if __name__ == "__main__":
    unittest.main()
