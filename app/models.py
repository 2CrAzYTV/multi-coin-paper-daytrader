from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    label: str
    short_allowed: bool
    max_leverage: float
    color: str


STRATEGIES = (
    StrategySpec("long_only_1x", "Long-only · 1×", False, 1.0, "#59d3a5"),
    StrategySpec("long_short_1x", "Long/Short · 1×", True, 1.0, "#66a7ff"),
    StrategySpec("long_short_2x", "Long/Short · max. 2×", True, 2.0, "#f4b860"),
)


@dataclass(frozen=True)
class PositionSize:
    units: float
    notional: float
    risk_budget: float
    estimated_stop_loss: float
    effective_leverage: float


@dataclass(frozen=True)
class PairConstraint:
    pair: str
    min_order_amount: float = 25.0
    max_order_amount: float = 1_000_000.0
    size_increment: float = 0.00000001


@dataclass(frozen=True)
class SignalSnapshot:
    pair: str
    candle_time: str
    price: float
    atr: float
    rsi: float
    direction: int
    trend: int
    strength: float
    reason: str
