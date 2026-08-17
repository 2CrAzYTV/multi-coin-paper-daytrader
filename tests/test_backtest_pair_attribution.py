import unittest

from app.backtest import SimAccount, _trade_diagnostics


class PairAttributionTests(unittest.TestCase):
    def test_pair_attribution_reports_trades_win_rate_pnl_and_side_split(self):
        account = SimAccount(balance=1000.0, peak=1000.0)
        account.trade_pnls = [12.0, -4.0, -3.0]
        account.long_trade_pnls = [12.0, -3.0]
        account.short_trade_pnls = [-4.0]
        account.pair_trade_pnls = {
            "BTC-EUR": [12.0, -4.0],
            "ETH-EUR": [-3.0],
        }
        account.pair_long_trade_pnls = {
            "BTC-EUR": [12.0],
            "ETH-EUR": [-3.0],
        }
        account.pair_short_trade_pnls = {"BTC-EUR": [-4.0]}

        result = _trade_diagnostics(account)

        self.assertEqual([row["pair"] for row in result["pair_attribution"]], ["BTC-EUR", "ETH-EUR"])
        btc = result["pair_attribution"][0]
        self.assertEqual(btc["trades"], 2)
        self.assertEqual(btc["wins"], 1)
        self.assertEqual(btc["win_rate_pct"], 50.0)
        self.assertEqual(btc["pnl_eur"], 8.0)
        self.assertEqual(btc["long_trades"], 1)
        self.assertEqual(btc["short_trades"], 1)
        self.assertEqual(btc["long_pnl_eur"], 12.0)
        self.assertEqual(btc["short_pnl_eur"], -4.0)

        eth = result["pair_attribution"][1]
        self.assertEqual(eth["trades"], 1)
        self.assertEqual(eth["win_rate_pct"], 0.0)
        self.assertEqual(eth["pnl_eur"], -3.0)
        self.assertEqual(eth["long_trades"], 1)
        self.assertEqual(eth["short_trades"], 0)

    def test_pair_attribution_is_empty_without_trades(self):
        account = SimAccount(balance=1000.0, peak=1000.0)
        result = _trade_diagnostics(account)
        self.assertEqual(result["pair_attribution"], [])


if __name__ == "__main__":
    unittest.main()
