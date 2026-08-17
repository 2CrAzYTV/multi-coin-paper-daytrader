import unittest
from datetime import UTC, datetime

from app.config import Settings
from app.market_data import INTERVAL_SECONDS, MarketData


class ShortPageFusionMarketData(MarketData):
    def __init__(self, settings):
        super().__init__(settings)
        self.calls = []
        self.interval = "15m"
        self.step = INTERVAL_SECONDS[self.interval]
        now = int(datetime.now(UTC).timestamp())
        self.latest_closed = ((now // self.step) - 2) * self.step

    def _get_json(self, path, params=None):
        self.calls.append(dict(params or {}))
        limit = int((params or {}).get("limit", 1000))
        to = (params or {}).get("to")
        end = int(to) if to is not None else self.latest_closed
        # Simulate Fusion returning at most 999 candles per page even when 1000
        # were requested and older history is still available.
        count = min(999, limit)
        start = end - (count - 1) * self.step
        return [
            {
                "timestamp": ts,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 10.0,
            }
            for ts in range(start, end + 1, self.step)
        ]


class FusionPaginationTests(unittest.TestCase):
    def test_short_pages_continue_until_requested_horizon_is_filled(self):
        settings = Settings(data_source="fusion", fusion_read_api_key="read-only-test")
        market = ShortPageFusionMarketData(settings)
        frame = market.history("BTC-EUR", "15m", 5000)

        self.assertEqual(len(frame), 5000)
        self.assertGreaterEqual(len(market.calls), 6)
        self.assertEqual(market.calls[0]["limit"], 1000)
        self.assertNotIn("to", market.calls[0])
        self.assertIn("to", market.calls[1])
        self.assertLess(market.calls[1]["to"], market.latest_closed)


if __name__ == "__main__":
    unittest.main()
