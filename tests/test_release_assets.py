import unittest
from struct import unpack
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ghcr.io/2crazytv/multi-coin-paper-daytrader:latest"
CENTRAL_CA_REPO = "https://github.com/2CrAzYTV/unraid-community-apps"
CENTRAL_TEMPLATE = (
    "https://raw.githubusercontent.com/2CrAzYTV/unraid-community-apps/"
    "main/templates/multi-coin-paper-daytrader.xml"
)


class ReleaseAssetTests(unittest.TestCase):
    def test_community_apps_reference_points_to_central_repository(self):
        guide = (ROOT / "COMMUNITY_APPS.md").read_text()
        self.assertIn(CENTRAL_CA_REPO, guide)
        self.assertIn(CENTRAL_TEMPLATE, guide)
        self.assertFalse((ROOT / "templates/multi-coin-paper-daytrader.xml").exists())
        self.assertFalse((ROOT / "ca_profile.xml").exists())

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
        self.assertNotIn("templates/multi-coin-paper-daytrader.xml", workflow)
        self.assertNotIn("Validate Community Applications template", workflow)

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
            "COMMUNITY_APPS.md",
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
            "COMMUNITY_APPS.md",
            ".github/CODEOWNERS",
            ".github/dependabot.yml",
            ".github/PULL_REQUEST_TEMPLATE.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
