import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ghcr.io/2crazytv/multi-coin-paper-daytrader:latest"


class ReleaseAssetTests(unittest.TestCase):
    def test_unraid_template_tracks_latest_with_hardened_runtime(self):
        root = ET.parse(ROOT / "unraid/multi-coin-paper-daytrader.xml").getroot()
        self.assertEqual(root.tag, "Container")
        self.assertEqual(root.findtext("Repository"), IMAGE)
        extra = root.findtext("ExtraParams") or ""
        for required in (
            "--user=99:100",
            "--read-only",
            "--security-opt=no-new-privileges:true",
            "--cap-drop=ALL",
            "--restart=unless-stopped",
        ):
            self.assertIn(required, extra)

    def test_main_workflow_publishes_updateable_latest_image(self):
        workflow = (ROOT / ".github/workflows/container-image.yml").read_text()
        self.assertIn("branches:\n      - main", workflow)
        self.assertIn("type=raw,value=latest,enable={{is_default_branch}}", workflow)
        self.assertIn("type=sha,prefix=sha-", workflow)
        self.assertIn("push: true", workflow)

    def test_public_unraid_guide_documents_update_and_persistence(self):
        guide = (ROOT / "docs/UNRAID.md").read_text()
        self.assertIn(IMAGE, guide)
        self.assertIn("Check for Updates", guide)
        self.assertIn("/mnt/user/appdata/paper-trading-bot/data", guide)
        self.assertIn("@sha256:", guide)
        self.assertIn("latest completed 15-minute Fusion candle", guide)
        self.assertIn("Reset my paper accounts → Delete paper data", guide)
        self.assertNotIn("docker login ghcr.io", guide)

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
            "unraid/multi-coin-paper-daytrader.xml",
            "app/static/index.html",
            "app/static/app.js",
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
        self.assertIn("${formatMarketPrice(item.price)}", javascript)

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
