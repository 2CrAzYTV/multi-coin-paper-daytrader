from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEV_TEMPLATE = ROOT / "dev-unraid/multi-coin-paper-daytrader-dev.xml.txt"
LEGACY_DEV_TEMPLATE = ROOT / "development/unraid-develop-template.txt"


def _variables(path: Path) -> dict[str, ET.Element]:
    root = ET.parse(path).getroot()
    return {
        item.attrib["Target"]: item
        for item in root.findall("Config")
        if item.attrib.get("Type") == "Variable"
    }


def test_dev_templates_replace_pairs_with_automatic_coin_scan():
    for path in (DEV_TEMPLATE, LEGACY_DEV_TEMPLATE):
        variables = _variables(path)
        assert "PAIRS" not in variables
        assert "AUTO_COIN_SCAN" in variables
        assert variables["AUTO_COIN_SCAN"].attrib["Default"] == "true"


def test_runtime_refreshes_fusion_universe_before_manual_scan_and_backtest():
    source = (ROOT / "app/main.py").read_text()
    assert 'getenv("AUTO_COIN_SCAN", "true")' in source
    assert "market.available_eur_pairs()" in source
    assert 'object.__setattr__(settings, "pairs", tuple(discovered))' in source
    assert source.count("await asyncio.to_thread(_refresh_coin_universe)") >= 2
    assert '"discovered_count": len(settings.pairs)' in source


def test_compose_uses_automatic_scan_not_manual_pairs():
    compose = (ROOT / "docker-compose.yml").read_text()
    assert 'AUTO_COIN_SCAN: "${AUTO_COIN_SCAN:-true}"' in compose
    assert "      PAIRS:" not in compose
    assert 'BACKTEST_BARS: "${BACKTEST_BARS:-5000}"' in compose
