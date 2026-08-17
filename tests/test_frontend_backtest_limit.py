import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendBacktestLimitTests(unittest.TestCase):
    def test_dashboard_honors_configured_backtest_bars_up_to_5000(self):
        diagnostics = (ROOT / "app/static/backtest-diagnostics.js").read_text()
        self.assertIn("Number(state.config.backtest_bars)", diagnostics)
        self.assertIn("Math.min(5000", diagnostics)
        self.assertIn("JSON.stringify({ bars: configuredBars })", diagnostics)
        self.assertIn("event.stopImmediatePropagation()", diagnostics)


if __name__ == "__main__":
    unittest.main()
