from __future__ import annotations

import math
from typing import Any

import pandas as pd

from .backtest import Backtester
from .market_data import MarketDataError
from .models import STRATEGIES, PairConstraint, StrategySpec


class WalkForwardBacktester(Backtester):
    """Backtester with a simple train/validation coin-selection comparison.

    Coin ranking is learned only on the earlier 60% of timestamps. The selected
    subsets are then evaluated on the later 40%, so the displayed selector
    comparison is out-of-sample relative to the ranking step.
    """

    TRAIN_FRACTION = 0.60
    SELECTOR_SIZES = (10, 7, 5, 3)
    MIN_RESEARCH_BARS = 1_000
    MIN_HISTORY_COVERAGE = 0.80

    @classmethod
    def required_history_bars(cls, selected_bars: int) -> int:
        """Require enough history for a meaningful train/validation split.

        For the normal 5,000-candle research horizon this requires at least
        4,000 usable candles. Shorter research runs still require at least 1,000
        candles when the requested horizon allows it.
        """
        coverage_target = math.ceil(selected_bars * cls.MIN_HISTORY_COVERAGE)
        return min(selected_bars, max(cls.MIN_RESEARCH_BARS, coverage_target))

    def run(self, bars: int | None = None) -> dict[str, Any]:
        selected_bars = min(5_000, bars or self.settings.backtest_bars)
        minimum_history = self.required_history_bars(selected_bars)
        constraints = self.market.pair_constraints()
        frames: dict[str, pd.DataFrame] = {}
        failures: dict[str, str] = {}
        skipped: dict[str, str] = {}
        history_counts: dict[str, int] = {}
        for pair in self.settings.pairs:
            if pair not in constraints:
                skipped[pair] = "not active"
                continue
            try:
                frame = self.market.history(pair, self.settings.candle_interval, selected_bars)
                history_counts[pair] = len(frame)
                if len(frame) < minimum_history:
                    skipped[pair] = (
                        f"insufficient history: {len(frame)} candles; "
                        f"at least {minimum_history} required"
                    )
                    continue
                frames[pair] = self._prepare(frame)
            except MarketDataError as exc:
                skipped[pair] = str(exc)
            except Exception as exc:
                failures[pair] = str(exc)
        if not frames:
            raise MarketDataError(
                "I found no pair with enough historical data for the multi-coin backtest."
            )

        timestamps = sorted(set().union(*(set(frame.index) for frame in frames.values())))
        results = [self._run_strategy(spec, frames, constraints, timestamps) for spec in STRATEGIES]
        benchmark = self._benchmark(frames, timestamps)
        selector = self._walk_forward_selector(frames, constraints, timestamps)
        return {
            "status": "ok",
            "pairs": sorted(frames),
            "failures": failures,
            "skipped_pairs": skipped,
            "history_counts": history_counts,
            "minimum_history_bars": minimum_history,
            "requested_bars": selected_bars,
            "from": pd.Timestamp(timestamps[0]).isoformat(),
            "to": pd.Timestamp(timestamps[-1]).isoformat(),
            "bars": len(timestamps),
            "data_source": self.settings.data_source,
            "strategies": results,
            "benchmark": benchmark,
            "coin_selector": selector,
            "liquidation_model": "paper-isolated-margin-estimate",
            "signal_model": "quality-filtered-ema-trend-v2",
        }

    def _walk_forward_selector(
        self,
        frames: dict[str, pd.DataFrame],
        constraints: dict[str, PairConstraint],
        timestamps: list[pd.Timestamp],
    ) -> dict[str, Any]:
        if len(timestamps) < 200 or len(frames) < 3:
            return {
                "status": "insufficient_data",
                "reason": "At least 200 timestamps and 3 pairs are required.",
            }

        split_index = max(100, min(len(timestamps) - 100, int(len(timestamps) * self.TRAIN_FRACTION)))
        train_timestamps = timestamps[:split_index]
        validation_timestamps = timestamps[split_index:]
        reference = self._selector_reference_strategy()

        training = self._run_strategy(reference, frames, constraints, train_timestamps)
        attribution = {row["pair"]: row for row in training.get("pair_attribution", [])}

        ranking: list[dict[str, Any]] = []
        for pair in sorted(frames):
            row = attribution.get(pair, {})
            trades = int(row.get("trades", 0) or 0)
            pnl = float(row.get("pnl_eur", 0.0) or 0.0)
            win_rate = float(row.get("win_rate_pct", 0.0) or 0.0)
            average_pnl = float(row.get("average_pnl_eur", 0.0) or 0.0)
            score = pnl + min(trades, 20) * 0.01 + average_pnl * 0.001 + win_rate * 0.0001
            ranking.append(
                {
                    "pair": pair,
                    "score": round(score, 4),
                    "training_pnl_eur": round(pnl, 2),
                    "training_trades": trades,
                    "training_win_rate_pct": round(win_rate, 1),
                }
            )
        ranking.sort(key=lambda item: (-item["score"], item["pair"]))

        requested_sizes = []
        for size in self.SELECTOR_SIZES:
            normalized = min(size, len(ranking))
            if normalized >= 1 and normalized not in requested_sizes:
                requested_sizes.append(normalized)

        comparisons: list[dict[str, Any]] = []
        for size in requested_sizes:
            selected_pairs = [item["pair"] for item in ranking[:size]]
            selected_frames = {pair: frames[pair] for pair in selected_pairs}
            selected_constraints = {pair: constraints[pair] for pair in selected_pairs}
            result = self._run_strategy(
                reference,
                selected_frames,
                selected_constraints,
                validation_timestamps,
            )
            pf = result.get("profit_factor")
            bounded_pf = min(float(pf), 5.0) if pf is not None else 0.0
            selection_score = (
                float(result["total_return_pct"])
                - 0.5 * float(result["max_drawdown_pct"])
                + 0.05 * bounded_pf
            )
            comparisons.append(
                {
                    "size": size,
                    "pairs": selected_pairs,
                    "final_equity": result["final_equity"],
                    "total_return_pct": result["total_return_pct"],
                    "max_drawdown_pct": result["max_drawdown_pct"],
                    "trades": result["trades"],
                    "win_rate_pct": result["win_rate_pct"],
                    "profit_factor": result.get("profit_factor"),
                    "expectancy_eur": result.get("expectancy_eur"),
                    "selection_score": round(selection_score, 4),
                }
            )

        best = max(comparisons, key=lambda item: (item["selection_score"], item["size"]))
        for item in comparisons:
            item["recommended"] = item is best

        return {
            "status": "ok",
            "method": "60/40 chronological walk-forward holdout",
            "reference_strategy_id": reference.strategy_id,
            "reference_strategy_label": reference.label,
            "train_from": pd.Timestamp(train_timestamps[0]).isoformat(),
            "train_to": pd.Timestamp(train_timestamps[-1]).isoformat(),
            "validation_from": pd.Timestamp(validation_timestamps[0]).isoformat(),
            "validation_to": pd.Timestamp(validation_timestamps[-1]).isoformat(),
            "train_bars": len(train_timestamps),
            "validation_bars": len(validation_timestamps),
            "ranking": ranking,
            "comparisons": comparisons,
            "recommended_size": best["size"],
            "recommended_pairs": best["pairs"],
        }

    @staticmethod
    def _selector_reference_strategy() -> StrategySpec:
        for spec in STRATEGIES:
            if spec.short_allowed and spec.max_leverage == 1.0:
                return spec
        return STRATEGIES[0]
