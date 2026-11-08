from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    label: str
    color: str


STRATEGY = StrategySpec("trend_donchian", "Trend following · Donchian breakout", "#59d3a5")
STRATEGIES = (STRATEGY,)


@dataclass(frozen=True)
class PairConstraint:
    pair: str
    min_order_amount: float = 25.0
    max_order_amount: float = 1_000_000.0
    size_increment: float = 0.00000001


@dataclass(frozen=True)
class Fill:
    price: float
    units: float
    source: str  # "order_book" or "candle"


@dataclass(frozen=True)
class SignalSnapshot:
    """Decision for the latest CLOSED candle of one pair.

    ``direction``: 1 = close above the prior entry channel (buy signal),
    -1 = close below the prior exit channel (sell signal), 0 = nothing.
    """

    pair: str
    candle_time: str
    price: float
    atr: float
    entry_level: float
    exit_level: float
    direction: int
    strength: float
    reason: str
