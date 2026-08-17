import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LegalSafetyGuardTests(unittest.TestCase):
    def test_fusion_market_client_is_get_only(self):
        source = (ROOT / "app/market_data.py").read_text()
        tree = ast.parse(source)
        write_methods = {"post", "put", "patch", "delete"}
        called_write_methods = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in write_methods
        }
        self.assertEqual(called_write_methods, set())
        self.assertIn("client.get(path, params=params)", source)

    def test_fusion_client_contains_no_order_or_transfer_api_paths(self):
        source = (ROOT / "app/market_data.py").read_text().lower()
        forbidden_paths = (
            "/orders",
            "/order/",
            "/transfers",
            "/transfer/",
            "/withdrawals",
            "/withdrawal/",
            "/deposits",
            "/deposit/",
        )
        for path in forbidden_paths:
            self.assertNotIn(path, source)

    def test_market_client_exposes_no_real_money_method_names(self):
        source = (ROOT / "app/market_data.py").read_text()
        tree = ast.parse(source)
        method_names = {
            node.name.lower()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        forbidden_names = {
            "place_order",
            "create_order",
            "submit_order",
            "cancel_order",
            "transfer",
            "withdraw",
            "deposit",
            "trade",
        }
        self.assertTrue(method_names.isdisjoint(forbidden_names))

    def test_dashboard_displays_legal_safety_notice(self):
        html = (ROOT / "app/static/index.html").read_text()
        self.assertIn("Paper trading only · Nur Paper-Trading", html)
        self.assertIn("Simulated paper signals only", html)
        self.assertIn("no personalized investment advice", html)
        self.assertIn("no guaranteed returns", html)
        self.assertIn("no affiliation with Bitpanda", html)

    def test_public_disclaimer_covers_regulatory_boundaries(self):
        disclaimer = (ROOT / "DISCLAIMER.md").read_text()
        required = (
            "does **not** place real-money orders",
            "does not provide personalized recommendations",
            "simulated paper signals only",
            "no profit, return, income, or performance is guaranteed or promised",
            "Read** permission only",
            "Trade** and **Transfer** permissions disabled",
            "not affiliated with, endorsed by, sponsored by, or supported by Bitpanda",
        )
        for text in required:
            self.assertIn(text, disclaimer)

    def test_community_applications_profile_is_unambiguous(self):
        profile = (ROOT / "ca_profile.xml").read_text()
        self.assertIn("paper-only", profile)
        self.assertIn("cannot place real-money orders", profile)
        self.assertIn("does not provide personalized investment advice", profile)
        self.assertIn("no profit or return guarantee", profile)
        self.assertIn("simulated paper signals only", profile)
        self.assertIn("not affiliated with or endorsed by Bitpanda", profile)


if __name__ == "__main__":
    unittest.main()
