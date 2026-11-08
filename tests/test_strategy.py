import unittest

import numpy as np
import pandas as pd

from app.config import Settings
from app.strategies import add_channels, signal_snapshot


def _frame(closes):
    index = pd.date_range("2025-01-01", periods=len(closes), freq="1D", tz="UTC")
    close = pd.Series(closes, index=index, dtype=float)
    return pd.DataFrame(
        {"Open": close, "High": close + 1, "Low": close - 1, "Close": close, "Volume": 1.0},
        index=index,
    )


class StrategyTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(entry_window=5, exit_window=3, atr_window=3, history_bars=10)

    def test_breakout_needs_close_above_prior_high_only(self):
        data = add_channels(_frame([100] * 6 + [101.5, 100.5]), self.settings)
        # prior 5-day high is 101 -> 101.5 is a breakout
        self.assertEqual(int(data.iloc[6]["SIGNAL"]), 1)
        self.assertAlmostEqual(float(data.iloc[6]["ENTRY_LEVEL"]), 101.0)
        # the breakout candle raised the channel, 100.5 is not above 102.5
        self.assertEqual(int(data.iloc[7]["SIGNAL"]), 0)

    def test_exit_on_close_below_prior_low(self):
        data = add_channels(_frame([100] * 6 + [98.5]), self.settings)
        self.assertEqual(int(data.iloc[-1]["SIGNAL"]), -1)
        self.assertAlmostEqual(float(data.iloc[-1]["EXIT_LEVEL"]), 99.0)

    def test_channels_never_use_the_current_candle(self):
        closes = list(np.linspace(100, 120, 30))
        base = add_channels(_frame(closes), self.settings)
        spiked = closes[:-1] + [500.0]
        changed = add_channels(_frame(spiked), self.settings)
        self.assertEqual(float(base.iloc[-1]["ENTRY_LEVEL"]), float(changed.iloc[-1]["ENTRY_LEVEL"]))
        self.assertEqual(float(base.iloc[-1]["EXIT_LEVEL"]), float(changed.iloc[-1]["EXIT_LEVEL"]))

    def test_snapshot_reports_levels_and_reason(self):
        snapshot = signal_snapshot("BTC-EUR", _frame([100] * 6 + [103]), self.settings)
        self.assertEqual(snapshot.direction, 1)
        self.assertEqual(snapshot.reason, "Breakout above the entry channel")
        self.assertAlmostEqual(snapshot.entry_level, 101.0)
        self.assertGreater(snapshot.strength, 0)


if __name__ == "__main__":
    unittest.main()
