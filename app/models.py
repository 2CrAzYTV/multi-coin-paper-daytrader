from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    label: str
    short_allowed: bool
    max_leverage: float
    color: str


def _leverage_id(value: float) -> str:
    text = f"{value:g}".replace(".", "p")
    return f"long_short_{text}x"


def build_strategies(leverages: tuple[float, ...]) -> tuple[StrategySpec, ...]:
    """Build paper-only comparison strategies for configured leverage values."""
    palette = (
        "#66a7ff",
        "#f4b860",
        "#d88cff",
        "#70d6ff",
        "#ff9770",
        "#ffd670",
        "#e9ff70",
        "#9bde7e",
        "#c77dff",
        "#ff70a6",
    )
    specs: list[StrategySpec] = [
        StrategySpec("long_only_1x", "Long-only · 1×", False, 1.0, "#59d3a5")
    ]
    for index, leverage in enumerate(leverages):
        specs.append(
            StrategySpec(
                _leverage_id(leverage),
                f"Long/Short · max. {leverage:g}×",
                True,
                leverage,
                palette[index % len(palette)],
            )
        )
    return tuple(specs)


DEFAULT_LEVERAGES = (1.0, 2.0)
STRATEGIES = build_strategies(DEFAULT_LEVERAGES)


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
