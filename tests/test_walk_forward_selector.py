from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from app.models import PairConstraint
from app.walk_forward import WalkForwardBacktester


class StubSelectorBacktester(WalkForwardBacktester):
    def _run_strategy(self, spec, frames, constraints, timestamps):
        pairs = list(frames)
        # Training call contains the full 10-pair universe. Give each pair a
        # deterministic descending P/L so the selector ranking is testable.
        if len(pairs) == 10:
            attribution = []
            for index, pair in enumerate(sorted(pairs)):
                attribution.append(
                    {
                        "pair": pair,
                        "trades": 5,
                        "wins": 3,
                        "win_rate_pct": 60.0,
                        "pnl_eur": float(10 - index),
                        "average_pnl_eur": float(10 - index) / 5,
                    }
                )
            return {"pair_attribution": attribution}

        size = len(pairs)
        # Make Top-5 the validation winner after return/drawdown scoring.
        metrics = {
            7: (1.0, 2.0, 8, 1.1),
            5: (3.0, 1.0, 7, 1.5),
            3: (2.0, 1.0, 5, 1.4),
        }
        ret, dd, trades, pf = metrics[size]
        return {
            "final_equity": 1000 * (1 + ret / 100),
            "total_return_pct": ret,
            "max_drawdown_pct": dd,
            "trades": trades,
            "win_rate_pct": 50.0,
            "profit_factor": pf,
            "expectancy_eur": 1.0,
        }


def test_selector_uses_chronological_holdout_and_recommends_best_validation_basket():
    settings = SimpleNamespace()
    backtester = StubSelectorBacktester(settings, market=None)
    pairs = [f"C{index:02d}-EUR" for index in range(10)]
    frames = {pair: pd.DataFrame() for pair in pairs}
    constraints = {pair: PairConstraint(pair=pair) for pair in pairs}
    timestamps = list(pd.date_range("2026-01-01", periods=500, freq="15min", tz="UTC"))

    result = backtester._walk_forward_selector(frames, constraints, timestamps)

    assert result["status"] == "ok"
    assert result["train_bars"] == 300
    assert result["validation_bars"] == 200
    assert result["train_to"] < result["validation_from"]
    assert [row["size"] for row in result["comparisons"]] == [10, 7, 5, 3]
    assert result["recommended_size"] == 5
    assert len(result["recommended_pairs"]) == 5
    assert result["ranking"][0]["pair"] == "C00-EUR"


def test_selector_refuses_too_little_data():
    backtester = StubSelectorBacktester(SimpleNamespace(), market=None)
    pairs = ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
    frames = {pair: pd.DataFrame() for pair in pairs}
    constraints = {pair: PairConstraint(pair=pair) for pair in pairs}
    timestamps = list(pd.date_range("2026-01-01", periods=150, freq="15min", tz="UTC"))

    result = backtester._walk_forward_selector(frames, constraints, timestamps)
    assert result["status"] == "insufficient_data"
