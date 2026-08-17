import unittest
from pathlib import Path


class FrontendPairAttributionTests(unittest.TestCase):
    def test_backtest_diagnostics_renders_pair_attribution(self):
        source = Path("app/static/backtest-diagnostics.js").read_text(encoding="utf-8")
        self.assertIn("pair_attribution", source)
        self.assertIn("Coin-Auswertung", source)
        self.assertIn("win_rate_pct", source)
        self.assertIn("pnl_eur", source)
        self.assertIn("long_trades", source)
        self.assertIn("short_trades", source)


if __name__ == "__main__":
    unittest.main()
