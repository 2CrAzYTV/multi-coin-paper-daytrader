import unittest

from app.config import Settings
from app.risk import calculate_position_size, daily_limit_breached, drawdown


class RiskTests(unittest.TestCase):
    def test_position_size_includes_costs_and_stays_inside_half_percent(self):
        result = calculate_position_size(
            equity=1_000,
            entry_price=100,
            stop_distance=2,
            risk_rate=0.005,
            max_leverage=2,
            fee_rate=0.001,
            slippage_rate=0.0005,
        )
        self.assertLessEqual(result.estimated_stop_loss, 5.000001)
        self.assertLessEqual(result.notional, 2_000)
        self.assertLessEqual(result.effective_leverage, 2)

    def test_remaining_portfolio_exposure_caps_new_position(self):
        result = calculate_position_size(
            equity=1_000,
            entry_price=100,
            stop_distance=0.01,
            risk_rate=0.005,
            max_leverage=2,
            fee_rate=0,
            slippage_rate=0,
            max_notional=300,
        )
        self.assertAlmostEqual(result.notional, 300)

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

    def test_api_key_is_never_public(self):
        public = Settings(fusion_read_api_key="secret-value").public_dict()
        self.assertNotIn("fusion_read_api_key", public)
        self.assertTrue(public["fusion_key_configured"])
        self.assertNotIn("secret-value", repr(public))


if __name__ == "__main__":
    unittest.main()
