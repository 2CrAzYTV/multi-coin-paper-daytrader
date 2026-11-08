import unittest

from app.config import FUSION_ENTRY_TIER_FEE, Settings
from app.risk import drawdown, walk_order_book
from app.strategies import target_notional


class RiskTests(unittest.TestCase):
    def test_default_fee_is_the_fusion_entry_tier(self):
        self.assertEqual(Settings().fee_rate, FUSION_ENTRY_TIER_FEE)
        self.assertEqual(FUSION_ENTRY_TIER_FEE, 0.0025)

    def test_drawdown(self):
        self.assertAlmostEqual(drawdown(1_000, 900), 0.1)
        self.assertEqual(drawdown(1_000, 1_100), 0.0)

    def test_target_notional_is_equal_share_limited_by_cash(self):
        args = dict(pair_count=4, min_order_amount=30, max_order_amount=1e6, fee_rate=0.0025)
        self.assertAlmostEqual(target_notional(equity=1_000, cash=1_000, **args), 250)
        # spot: never more than the cash on hand (incl. the fee)
        self.assertAlmostEqual(target_notional(equity=1_000, cash=100, **args), 100 / 1.0025)
        # small account: equal share (25) is lifted to the exchange minimum
        self.assertAlmostEqual(target_notional(equity=100, cash=100, **args), 30.3)
        # not enough cash for the minimum -> no order
        self.assertEqual(target_notional(equity=100, cash=20, **args), 0.0)

    def test_order_book_walk_buys_through_levels(self):
        asks = [(100.0, 0.5), (101.0, 1.0)]
        price, units = walk_order_book(asks, notional=100.0)
        self.assertAlmostEqual(units, 0.5 + 50 / 101)
        self.assertGreater(price, 100.0)
        self.assertLess(price, 101.0)

    def test_order_book_walk_sells_units_and_rejects_thin_books(self):
        bids = [(99.0, 1.0), (98.0, 1.0)]
        price, units = walk_order_book(bids, units=1.5)
        self.assertAlmostEqual(units, 1.5)
        self.assertAlmostEqual(price, (99 + 49) / 1.5)
        self.assertIsNone(walk_order_book(bids, units=5))

    def test_configuration_is_paper_only(self):
        with self.assertRaises(ValueError):
            Settings(paper_only=False).validate()

    def test_configuration_rejects_bad_channels_and_positions(self):
        with self.assertRaises(ValueError):
            Settings(entry_window=20, exit_window=20).validate()
        with self.assertRaises(ValueError):
            Settings(max_open_positions=5).validate()
        with self.assertRaises(ValueError):
            Settings(candle_interval="15m").validate()

    def test_configuration_accepts_only_english_or_german(self):
        Settings(app_language="de").validate()
        with self.assertRaises(ValueError):
            Settings(app_language="fr").validate()

    def test_language_default_is_public_without_exposing_secrets(self):
        public = Settings(app_language="de", fusion_read_api_key="secret-value").public_dict()
        self.assertEqual(public["app_language"], "de")
        self.assertNotIn("fusion_read_api_key", public)

    def test_api_key_is_never_public(self):
        public = Settings(fusion_read_api_key="secret-value").public_dict()
        self.assertNotIn("fusion_read_api_key", public)
        self.assertTrue(public["fusion_key_configured"])
        self.assertNotIn("secret-value", repr(public))


if __name__ == "__main__":
    unittest.main()
