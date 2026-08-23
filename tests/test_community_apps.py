import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CENTRAL_REPO = "https://github.com/2CrAzYTV/unraid-community-apps"
CENTRAL_TEMPLATE = (
    "https://raw.githubusercontent.com/2CrAzYTV/unraid-community-apps/"
    "main/templates/multi-coin-paper-daytrader.xml"
)


class CommunityApplicationsTests(unittest.TestCase):
    def test_project_points_to_central_ca_repository(self):
        guide = (ROOT / "COMMUNITY_APPS.md").read_text()
        self.assertIn(CENTRAL_REPO, guide)
        self.assertIn(CENTRAL_TEMPLATE, guide)
        self.assertIn("canonical Community Applications metadata", guide)

    def test_project_no_longer_duplicates_ca_metadata(self):
        self.assertFalse((ROOT / "ca_profile.xml").exists())
        self.assertFalse((ROOT / "templates/multi-coin-paper-daytrader.xml").exists())
        self.assertFalse((ROOT / "templates/alarm-hub.xml").exists())
        self.assertFalse((ROOT / "templates/webcomm-calendar-sync.xml").exists())

    def test_central_reference_has_no_starter_placeholders(self):
        text = (ROOT / "COMMUNITY_APPS.md").read_text()
        for placeholder in (
            "YOUR_GITHUB_USERNAME",
            "YOUR_REPO_NAME",
            "YOUR_SUPPORT_TOPIC",
            "example-app",
        ):
            self.assertNotIn(placeholder, text)


if __name__ == "__main__":
    unittest.main()
