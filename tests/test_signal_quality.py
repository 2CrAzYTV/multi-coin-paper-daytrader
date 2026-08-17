import unittest

import pandas as pd

from app.config import Settings
from app.strategies import add_signal_columns, should_exit


class SignalQualityTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            signal_min_strength=0.10,
            trend_min_strength_pct=0.001,
            volume_multiplier=1.0,
            long_rsi_min=48,
            long_rsi_max=64,
            short_rsi_min=36,
            short_rsi_max=52,
            exit_confirmation_bars=2,
        )

    def _entry(self, long=True, weak=False, low_volume=False):
        index = pd.date_range("2026-08-17T08:00:00Z", periods=3, freq="15min")
        if long:
            fast = [99.0, 99.5, 101.0]
            slow = [100.0, 100.0, 100.0]
            close = [99.0, 100.0, 102.0]
            rsi = [45.0, 48.0, 55.0]
        else:
            fast = [101.0, 100.5, 99.0]
            slow = [100.0, 100.0, 100.0]
            close = [101.0, 100.0, 98.0]
            rsi = [55.0, 52.0, 45.0]
        strength = [0.2, 0.2, 0.05 if weak else 0.2]
        return pd.DataFrame(
            {
                "Open": close,
                "High": [value + 1 for value in close],
                "Low": [value - 1 for value in close],
                "Close": close,
                "Volume": [100, 100, 50 if low_volume else 120],
                "EMA_FAST": fast,
                "EMA_SLOW": slow,
                "ATR": [2.0, 2.0, 2.0],
                "RSI": rsi,
                "VOLUME_MEDIAN": [100.0, 100.0, 100.0],
                "EMA_STRENGTH": strength,
            },
            index=index,
        )

    def _trend(self, long=True, weak=False, wrong_slope=False):
        index = pd.date_range("2026-08-17T08:00:00Z", periods=2, freq="1h")
        if long:
            fast = [101.0, 102.0 if not wrong_slope else 100.0]
            slow = [100.0, 100.0]
            slope = [1.0, 1.0 if not wrong_slope else -1.0]
        else:
            fast = [99.0, 98.0 if not wrong_slope else 100.0]
            slow = [100.0, 100.0]
            slope = [-1.0, -1.0 if not wrong_slope else 1.0]
        return pd.DataFrame(
            {
                "TREND_FAST": fast,
                "TREND_SLOW": slow,
                "TREND_STRENGTH_PCT": [0.01, 0.0005 if weak else 0.01],
                "TREND_FAST_SLOPE": slope,
            },
            index=index,
        )

    def test_high_quality_long_signal_passes(self):
        result = add_signal_columns(self._entry(True), self._trend(True), self.settings)
        self.assertEqual(int(result.iloc[-1]["SIGNAL"]), 1)

    def test_high_quality_short_signal_passes(self):
        result = add_signal_columns(self._entry(False), self._trend(False), self.settings)
        self.assertEqual(int(result.iloc[-1]["SIGNAL"]), -1)

    def test_weak_or_low_volume_signal_is_rejected(self):
        weak = add_signal_columns(self._entry(True, weak=True), self._trend(True), self.settings)
        volume = add_signal_columns(
            self._entry(True, low_volume=True), self._trend(True), self.settings
        )
        trend = add_signal_columns(self._entry(True), self._trend(True, weak=True), self.settings)
        self.assertEqual(int(weak.iloc[-1]["SIGNAL"]), 0)
        self.assertEqual(int(volume.iloc[-1]["SIGNAL"]), 0)
        self.assertEqual(int(trend.iloc[-1]["SIGNAL"]), 0)

    def test_exit_requires_two_confirming_bars(self):
        frame = pd.DataFrame(
            {
                "EMA_FAST": [101.0, 99.0, 98.0],
                "EMA_SLOW": [100.0, 100.0, 100.0],
            }
        )
        self.assertTrue(should_exit(1, frame, 2))
        frame.loc[1, "EMA_FAST"] = 101.0
        self.assertFalse(should_exit(1, frame, 2))

    def test_quality_settings_validate(self):
        self.settings.validate()
        with self.assertRaises(ValueError):
            Settings(volume_multiplier=4).validate()
        with self.assertRaises(ValueError):
            Settings(exit_confirmation_bars=0).validate()


if __name__ == "__main__":
    unittest.main()
