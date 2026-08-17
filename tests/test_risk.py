import unittest

from app.config import Settings
from app.risk import (
    calculate_position_size,
    daily_limit_breached,
    drawdown,
    estimate_liquidation_price,
    margin_required,
    margin_utilization,
)


class RiskTests(unittest.TestCase):
    def test_position_size_includes_costs_and_stays_inside_half_percent(self):
        result = calculate_position_size(
            equity=1_000,
            entry_price=100,
            stop_distance=2,
            risk_rate=0.005,
            max_leverage=10,
            fee_rate=0.001,
            slippage_rate=0.0005,
        )
        self.assertLessEqual(result.estimated_stop_loss, 5.000001)
        self.assertLessEqual(result.notional, 10_000)
        self.assertLessEqual(result.effective_leverage, 10)

    def test_higher_leverage_does_not_increase_risk_budget(self):
        low = calculate_position_size(
            equity=1_000,
            entry_price=100,
            stop_distance=2,
            risk_rate=0.005,
            max_leverage=2,
            fee_rate=0.001,
            slippage_rate=0.0005,
        )
        high = calculate_position_size(
            equity=1_000,
            entry_price=100,
            stop_distance=2,
            risk_rate=0.005,
            max_leverage=10,
            fee_rate=0.001,
            slippage_rate=0.0005,
        )
        self.assertAlmostEqual(low.risk_budget, 5.0)
        self.assertAlmostEqual(high.risk_budget, 5.0)
        self.assertLessEqual(high.estimated_stop_loss, 5.000001)

    def test_remaining_portfolio_exposure_caps_new_position(self):
        result = calculate_position_size(
            equity=1_000,
            entry_price=100,
            stop_distance=0.01,
            risk_rate=0.005,
            max_leverage=10,
            fee_rate=0,
            slippage_rate=0,
            max_notional=300,
        )
        self.assertAlmostEqual(result.notional, 300)

    def test_entry_cost_reserve_keeps_one_x_below_full_margin(self):
        result = calculate_position_size(
            equity=1_000,
            entry_price=100,
            stop_distance=0.01,
            risk_rate=1.0,
            max_leverage=1,
            fee_rate=0.001,
            slippage_rate=0.0005,
            max_notional=1_000,
        )
        post_fee_equity = 1_000 - result.notional * 0.001
        marked_notional = result.notional * 1.0005
        self.assertLessEqual(marked_notional / post_fee_equity, 1.0 + 1e-9)
        self.assertLessEqual(margin_utilization(marked_notional, post_fee_equity, 1), 1.0 + 1e-9)

    def test_entry_cost_reserve_scales_with_leverage(self):
        result = calculate_position_size(
            equity=1_000,
            entry_price=100,
            stop_distance=0.01,
            risk_rate=1.0,
            max_leverage=10,
            fee_rate=0.001,
            slippage_rate=0.0005,
            max_notional=10_000,
        )
        post_fee_equity = 1_000 - result.notional * 0.001
        marked_notional = result.notional * 1.0005
        self.assertLessEqual(marked_notional / post_fee_equity, 10.0 + 1e-9)
        self.assertLessEqual(margin_utilization(marked_notional, post_fee_equity, 10), 1.0 + 1e-9)

    def test_margin_math(self):
        self.assertAlmostEqual(margin_required(5_000, 10), 500)
        self.assertAlmostEqual(margin_utilization(5_000, 1_000, 10), 0.5)
        self.assertAlmostEqual(margin_required(500, 1), 500)

    def test_liquidation_estimate_is_directional_and_disabled_at_one_x(self):
        self.assertIsNone(estimate_liquidation_price(100, 1, 1))
        long_price = estimate_liquidation_price(100, 1, 10)
        short_price = estimate_liquidation_price(100, -1, 10)
        self.assertIsNotNone(long_price)
        self.assertIsNotNone(short_price)
        self.assertLess(long_price, 100)
        self.assertGreater(short_price, 100)
        self.assertAlmostEqual(long_price, 90.5)
        self.assertAlmostEqual(short_price, 109.5)

    def test_liquidation_distance_tightens_as_leverage_increases(self):
        two_x = estimate_liquidation_price(100, 1, 2)
        ten_x = estimate_liquidation_price(100, 1, 10)
        self.assertLess(two_x, ten_x)

    def test_daily_limit_and_drawdown(self):
        self.assertFalse(daily_limit_breached(1_000, 981, 0.02))
        self.assertTrue(daily_limit_breached(1_000, 980, 0.02))
        self.assertAlmostEqual(drawdown(1_000, 900), 0.1)

    def test_configuration_rejects_more_than_one_percent_trade_risk(self):
        settings = Settings(risk_per_trade=0.011)
        with self.assertRaises(ValueError):
            settings.validate()

    def test_configuration_rejects_more_than_two_percent_daily_loss(self):
        settings = Settings(max_daily_loss=0.021)
        with self.assertRaises(ValueError):
            settings.validate()

    def test_configuration_is_paper_only(self):
        settings = Settings(paper_only=False)
        with self.assertRaises(ValueError):
            settings.validate()

    def test_configuration_accepts_only_english_or_german(self):
        Settings(app_language="en").validate()
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
