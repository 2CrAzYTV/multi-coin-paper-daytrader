import unittest
import xml.etree.ElementTree as ET
from struct import unpack
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ghcr.io/2crazytv/multi-coin-paper-daytrader:latest"
CA_TEMPLATE = ROOT / "templates/multi-coin-paper-daytrader.xml"


class ReleaseAssetTests(unittest.TestCase):
    def test_unraid_template_tracks_latest_with_hardened_runtime(self):
        root = ET.parse(CA_TEMPLATE).getroot()
        self.assertEqual(root.tag, "Container")
        self.assertEqual(root.findtext("Name"), "Multi-Coin Paper Daytrader")
        self.assertEqual(root.findtext("Repository"), IMAGE)
        self.assertEqual(
            root.findtext("Icon"),
            "https://raw.githubusercontent.com/2CrAzYTV/"
            "multi-coin-paper-daytrader/main/unraid/multi-coin-paper-daytrader.png",
        )
        self.assertEqual(
            root.findtext("TemplateURL"),
            "https://raw.githubusercontent.com/2CrAzYTV/"
            "multi-coin-paper-daytrader/main/templates/multi-coin-paper-daytrader.xml",
        )
        extra = root.findtext("ExtraParams") or ""
        for required in (
            "--user=99:100",
            "--read-only",
            "--init",
            "--tmpfs=/tmp:size=64m,mode=1777",
            "--security-opt=no-new-privileges:true",
            "--cap-drop=ALL",
            "--pids-limit=2048",
            "--restart=unless-stopped",
            "--stop-timeout=20",
        ):
            self.assertIn(required, extra)
        self.assertNotIn("--env-file=", extra)

        configs = root.findall("Config")
        variables = {
            item.attrib["Target"]: item for item in configs if item.attrib["Type"] == "Variable"
        }
        required_defaults = {
            "PAPER_ONLY": "true",
            "STARTING_CAPITAL": "1000",
            "RISK_PER_TRADE": "0.005",
            "MAX_AGGREGATE_RISK": "0.01",
            "MAX_DAILY_LOSS": "0.02",
            "HARD_DRAWDOWN": "0.10",
            "MAX_OPEN_POSITIONS": "2",
            "MAX_TRADES_PER_DAY": "3",
            "FEE_RATE": "0.001",
            "SLIPPAGE_RATE": "0.0005",
            "PAIRS": "BTC-EUR,ETH-EUR,SOL-EUR,XRP-EUR,ADA-EUR",
            "CANDLE_INTERVAL": "15m",
            "TREND_INTERVAL": "1h",
            "FAST_WINDOW": "9",
            "SLOW_WINDOW": "21",
            "TREND_FAST_WINDOW": "20",
            "TREND_SLOW_WINDOW": "50",
            "ATR_WINDOW": "14",
            "RSI_WINDOW": "14",
            "STOP_ATR_MULTIPLE": "1.5",
            "MINIMUM_STOP_PCT": "0.006",
            "TAKE_PROFIT_R": "2.0",
            "TRAILING_TRIGGER_R": "1.0",
            "HISTORY_BARS": "500",
            "BACKTEST_BARS": "1000",
            "DATA_SOURCE": "demo",
            "FUSION_BASE_URL": "https://api.fusion.bitpanda.com",
            "APP_TIMEZONE": "Europe/Berlin",
            "POLL_SECONDS": "60",
            "SESSION_CLOSE_HOUR": "23",
            "SESSION_CLOSE_MINUTE": "45",
            "COOLDOWN_MINUTES": "45",
            "APP_LANGUAGE": "de",
            "DATA_DIR": "/data",
            "TZ": "Europe/Berlin",
        }
        for target, expected in required_defaults.items():
            self.assertIn(target, variables)
            self.assertEqual(variables[target].attrib["Default"], expected)

        for compose_only in ("WEB_PORT", "PUID", "PGID"):
            self.assertNotIn(compose_only, variables)

        self.assertIn("FUSION_READ_API_KEY", variables)
        self.assertEqual(variables["FUSION_READ_API_KEY"].attrib["Mask"], "true")
        self.assertEqual(variables["FUSION_READ_API_KEY"].attrib["Default"], "")
        self.assertEqual(variables["FUSION_READ_API_KEY"].attrib["Name"], "Bitpanda Key")
        self.assertEqual(
            {item.attrib["Target"] for item in configs if item.attrib["Type"] == "Path"},
            {"/data"},
        )

        overview = root.findtext("Overview") or ""
        requires = root.findtext("Requires") or ""
        self.assertIn("paper-only", overview)
        self.assertIn("cannot place real-money orders", overview)
        self.assertIn("PAPER_ONLY=true", requires)
        self.assertIn("Read permission only", requires)
        self.assertIn("Trade and Transfer disabled", requires)

    def test_compose_has_safe_defaults_without_env_file_dependency(self):
        compose = (ROOT / "docker-compose.yml").read_text()
        self.assertNotIn("env_file:", compose)
        self.assertIn('PAPER_ONLY: "${PAPER_ONLY:-true}"', compose)
        self.assertIn('DATA_SOURCE: "${DATA_SOURCE:-demo}"', compose)
        self.assertIn('FUSION_READ_API_KEY: "${FUSION_READ_API_KEY:-}"', compose)
        self.assertIn('${WEB_PORT:-8787}:8787', compose)
        self.assertIn('${PUID:-99}:${PGID:-100}', compose)

    def test_version_is_consistent(self):
        package = (ROOT / "app/__init__.py").read_text()
        main = (ROOT / "app/main.py").read_text()
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn('__version__ = "0.2.0"', package)
        self.assertIn('version="0.2.0"', main)
        self.assertIn('org.opencontainers.image.version="0.2.0"', dockerfile)

    def test_unraid_icon_is_high_resolution_transparent_png(self):
        icon = (ROOT / "unraid/multi-coin-paper-daytrader.png").read_bytes()
        self.assertEqual(icon[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(unpack(">II", icon[16:24]), (512, 512))
        self.assertEqual(icon[25], 6, "I require an RGBA PNG with transparency.")
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn(
            "COPY unraid/multi-coin-paper-daytrader.png ./app/static/app-icon.png",
            dockerfile,
        )

    def test_main_workflow_publishes_updateable_latest_image(self):
        workflow = (ROOT / ".github/workflows/container-image.yml").read_text()
        self.assertIn("branches:\n      - main", workflow)
        self.assertIn("type=raw,value=latest,enable={{is_default_branch}}", workflow)
        self.assertIn("type=sha,prefix=sha-", workflow)
        self.assertIn("push: true", workflow)
        self.assertIn("templates/multi-coin-paper-daytrader.xml", workflow)
        self.assertNotIn("ET.parse('unraid/multi-coin-paper-daytrader.xml')", workflow)

    def test_public_unraid_guide_documents_update_and_persistence(self):
        guide = (ROOT / "docs/UNRAID.md").read_text()
        self.assertIn(IMAGE, guide)
        self.assertIn("Check for Updates", guide)
        self.assertIn("/mnt/user/appdata/paper-trading-bot/data", guide)
        self.assertIn("@sha256:", guide)
        self.assertIn("latest completed 15-minute Fusion candle", guide)
        self.assertIn("Reset my paper accounts → Delete paper data", guide)
        self.assertIn("--pids-limit=2048", guide)
        self.assertIn("APP_LANGUAGE=de", guide)
        self.assertIn("A separate `.env` file is not required", guide)
        self.assertIn("locally saved template", guide)

    def test_public_facing_assets_are_english(self):
        paths = (
            "README.md",
            "CHANGELOG.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CONTRIBUTING.md",
            "DISCLAIMER.md",
            "CODE_OF_CONDUCT.md",
            "docs/UNRAID.md",
            "templates/multi-coin-paper-daytrader.xml",
            "app/static/index.html",
        )
        german_markers = ("Veröffentlichungsstatus", "Jetzt prüfen", "Noch keine")
        for relative in paths:
            content = (ROOT / relative).read_text()
            for marker in german_markers:
                self.assertNotIn(marker, content, relative)
        self.assertIn('<html lang="en">', (ROOT / "app/static/index.html").read_text())

    def test_market_prices_keep_sub_euro_precision(self):
        javascript = (ROOT / "app/static/app.js").read_text()
        self.assertIn("function formatMarketPrice(value)", javascript)
        self.assertIn("minimumFractionDigits: 4, maximumFractionDigits: 4", javascript)
        self.assertIn("minimumFractionDigits: 6, maximumFractionDigits: 6", javascript)
        self.assertIn("formatMarketPrice(item.price)", javascript)
        self.assertIn("formatMarketPrice(item.stop_price)", javascript)

    def test_dashboard_supports_persistent_english_and_german(self):
        html = (ROOT / "app/static/index.html").read_text()
        javascript = (ROOT / "app/static/app.js").read_text()
        environment = (ROOT / ".env.example").read_text()
        self.assertIn('id="languageSelect"', html)
        self.assertIn('<option value="en">English</option>', html)
        self.assertIn('<option value="de">Deutsch</option>', html)
        self.assertIn('const supportedLanguages = new Set(["en", "de"]);', javascript)
        self.assertIn('window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language)', javascript)
        self.assertIn('state.config.app_language', javascript)
        self.assertIn('state.language === "de" ? "de-DE" : "en-GB"', javascript)
        self.assertIn("APP_LANGUAGE=en", environment)

    def test_release_policy_files_exist(self):
        for relative in (
            "LICENSE",
            "DISCLAIMER.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            ".github/CODEOWNERS",
            ".github/dependabot.yml",
            ".github/PULL_REQUEST_TEMPLATE.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
