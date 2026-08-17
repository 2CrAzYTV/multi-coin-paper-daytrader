from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_backtest_requires_meaningful_history_and_reports_skips():
    source = (ROOT / "app/backtest.py").read_text()
    assert "minimum_history_bars = max(100, math.floor(selected_bars * 0.95))" in source
    assert '"skipped_pairs": skipped' in source
    assert '"quality_filter"' in source
    assert '"minimum_history_bars": minimum_history_bars' in source


def test_api_exposes_coin_scan_quality_counts():
    source = (ROOT / "app/main.py").read_text()
    assert 'skipped = result.get("skipped_pairs", {})' in source
    assert '"skipped_count": len(skipped)' in source
    assert '"skipped_pairs": skipped' in source
    assert '"usable_count": len(result.get("pairs", []))' in source
