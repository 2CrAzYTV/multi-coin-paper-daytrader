import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ghcr.io/2crazytv/multi-coin-paper-daytrader:latest"
TEMPLATE_URL = (
    "https://raw.githubusercontent.com/2CrAzYTV/multi-coin-paper-daytrader/"
    "main/templates/multi-coin-paper-daytrader.xml"
)
ICON_URL = (
    "https://raw.githubusercontent.com/2CrAzYTV/multi-coin-paper-daytrader/"
    "main/unraid/multi-coin-paper-daytrader.png"
)


class CommunityApplicationsTests(unittest.TestCase):
    def test_ca_profile_has_required_public_metadata(self):
        root = ET.parse(ROOT / "ca_profile.xml").getroot()
        self.assertEqual(root.tag, "CommunityApplications")
        profile = (root.findtext("Profile") or "").strip()
        self.assertGreater(len(profile), 80)
        self.assertIn("paper-only", profile.lower())
        self.assertEqual(root.findtext("Icon"), ICON_URL)
        self.assertEqual(
            root.findtext("WebPage"),
            "https://github.com/2CrAzYTV/multi-coin-paper-daytrader",
        )
        self.assertEqual(
            root.findtext("Forum"),
            "https://github.com/2CrAzYTV/multi-coin-paper-daytrader/issues",
        )

    def test_ca_docker_template_is_submission_ready(self):
        root = ET.parse(ROOT / "templates/multi-coin-paper-daytrader.xml").getroot()
        self.assertEqual(root.tag, "Container")
        self.assertEqual(root.attrib.get("version"), "2")
        self.assertEqual(root.findtext("Name"), "Multi-Coin Paper Daytrader")
        self.assertEqual(root.findtext("Repository"), IMAGE)
        self.assertEqual(root.findtext("TemplateURL"), TEMPLATE_URL)
        self.assertEqual(root.findtext("Icon"), ICON_URL)
        self.assertEqual(root.findtext("Beta"), "true")
        self.assertIn("Tools:Utilities", root.findtext("Category") or "")
        self.assertIn("Crypto Currency", root.findtext("Category") or "")
        self.assertTrue((root.findtext("Overview") or "").strip())
        self.assertTrue((root.findtext("Support") or "").startswith("https://"))
        self.assertTrue((root.findtext("Project") or "").startswith("https://"))
        self.assertNotIn("--env-file=", root.findtext("ExtraParams") or "")

        configs = root.findall("Config")
        self.assertEqual(len(configs), 38)
        variables = {
            item.attrib["Target"]: item
            for item in configs
            if item.attrib.get("Type") == "Variable"
        }
        self.assertEqual(variables["PAPER_ONLY"].attrib["Default"], "true")
        self.assertEqual(variables["DATA_SOURCE"].attrib["Default"], "demo")
        self.assertEqual(variables["FUSION_READ_API_KEY"].attrib["Mask"], "true")
        self.assertEqual(variables["FUSION_READ_API_KEY"].attrib["Default"], "")

    def test_ca_files_have_no_starter_placeholders(self):
        for relative in (
            "ca_profile.xml",
            "templates/multi-coin-paper-daytrader.xml",
        ):
            text = (ROOT / relative).read_text()
            for placeholder in (
                "YOUR_GITHUB_USERNAME",
                "YOUR_REPO_NAME",
                "YOUR_SUPPORT_TOPIC",
                "example-app",
            ):
                self.assertNotIn(placeholder, text, relative)


if __name__ == "__main__":
    unittest.main()
