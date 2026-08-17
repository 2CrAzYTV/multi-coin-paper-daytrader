import unittest

from app.backtest import Backtester
from app.config import Settings
from app.market_data import MarketDataError
from app.models import PairConstraint


class RecordingMarket:
    def __init__(self):
        self.requested_limits = []

    def pair_constraints(self):
        return {"BTC-EUR": PairConstraint(pair="BTC-EUR")}

    def history(self, pair, interval, limit):
        self.requested_limits.append(limit)
        raise RuntimeError("stop after recording requested horizon")


class BacktesterHorizonTests(unittest.TestCase):
    def test_backtester_passes_configured_5000_bar_horizon_to_market_data(self):
        settings = Settings(pairs=("BTC-EUR",), backtest_bars=5000)
        market = RecordingMarket()

        with self.assertRaises(MarketDataError):
            Backtester(settings, market).run()

        self.assertEqual(market.requested_limits, [5000])

    def test_backtester_caps_manual_horizon_at_5000(self):
        settings = Settings(pairs=("BTC-EUR",), backtest_bars=5000)
        market = RecordingMarket()

        with self.assertRaises(MarketDataError):
            Backtester(settings, market).run(9000)

        self.assertEqual(market.requested_limits, [5000])


if __name__ == "__main__":
    unittest.main()
