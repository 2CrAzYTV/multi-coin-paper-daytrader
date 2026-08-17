from __future__ import annotations

from .models import PositionSize


def calculate_position_size(
    *,
    equity: float,
    entry_price: float,
    stop_distance: float,
    risk_rate: float,
    max_leverage: float,
    fee_rate: float,
    slippage_rate: float,
    max_notional: float | None = None,
) -> PositionSize:
    """Size a position so the modeled stop loss stays inside the risk budget.

    Round-trip fees and adverse slippage are included in the estimate. A real
    market gap can still exceed the estimate, which is why this is a risk cap,
    not a guarantee.
    """
    if equity <= 0 or entry_price <= 0 or stop_distance <= 0:
        return PositionSize(0.0, 0.0, 0.0, 0.0, 0.0)

    risk_budget = equity * risk_rate
    round_trip_cost_per_unit = entry_price * 2 * (fee_rate + slippage_rate)
    modeled_loss_per_unit = stop_distance + round_trip_cost_per_unit
    units_by_risk = risk_budget / modeled_loss_per_unit
    exposure_cap = equity * max_leverage
    if max_notional is not None:
        exposure_cap = min(exposure_cap, max(0.0, max_notional))
    units_by_exposure = exposure_cap / entry_price
    units = max(0.0, min(units_by_risk, units_by_exposure))
    notional = units * entry_price
    modeled_loss = units * modeled_loss_per_unit
    effective_leverage = notional / equity if equity else 0.0
    return PositionSize(
        units=units,
        notional=notional,
        risk_budget=risk_budget,
        estimated_stop_loss=modeled_loss,
        effective_leverage=effective_leverage,
    )


def daily_limit_breached(
    day_start_equity: float, current_equity: float, maximum_loss_rate: float
) -> bool:
    if day_start_equity <= 0:
        return True
    return current_equity <= day_start_equity * (1 - maximum_loss_rate)


def drawdown(peak_equity: float, current_equity: float) -> float:
    if peak_equity <= 0:
        return 1.0
    return max(0.0, (peak_equity - current_equity) / peak_equity)
