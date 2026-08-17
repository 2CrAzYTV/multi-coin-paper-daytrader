from pathlib import Path

from app.walk_forward import WalkForwardBacktester


ROOT = Path(__file__).resolve().parents[1]


def test_research_history_filter_requires_meaningful_coverage():
    assert WalkForwardBacktester.required_history_bars(5_000) == 4_000
    assert WalkForwardBacktester.required_history_bars(2_000) == 1_600
    assert WalkForwardBacktester.required_history_bars(1_000) == 1_000
    assert WalkForwardBacktester.required_history_bars(500) == 500


def test_walk_forward_exposes_skipped_pairs_separately_from_real_failures():
    source = (ROOT / "app/walk_forward.py").read_text()
    assert '"skipped_pairs": skipped' in source
    assert '"minimum_history_bars": minimum_history' in source
    assert 'except MarketDataError as exc:' in source
    assert 'skipped[pair] = str(exc)' in source


def test_dashboard_has_distinct_scan_and_backtest_progress_bars():
    source = (ROOT / "app/static/backtest-diagnostics.js").read_text()
    assert 'progressFor(button, "scanProgress")' in source
    assert 'progressFor(button, "backtestProgress")' in source
    assert 'operation-progress running' in source or '"running"' in source
    assert 'Backtest fertig' in source
    assert 'Scan fertig' in source
    assert 'event.stopImmediatePropagation()' in source
