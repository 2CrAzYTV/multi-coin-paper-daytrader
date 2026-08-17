from pathlib import Path


def test_frontend_renders_walk_forward_selector_comparison():
    source = Path("app/static/backtest-diagnostics.js").read_text(encoding="utf-8")
    assert "coinSelectorPanel" in source
    assert "selector.comparisons" in source
    assert "recommended" in source
    assert "60%" in source or "60 %" in source
    assert "Validation return" in source
