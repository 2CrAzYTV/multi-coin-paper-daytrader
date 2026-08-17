from __future__ import annotations

from .models import PositionSize


# Paper-only approximation used for isolated-margin liquidation estimates.
# This is deliberately not presented as Bitpanda's exact liquidation formula.
PAPER_MAINTENANCE_MARGIN_RATE = 0.005


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
    """Size a position so risk and post-cost leverage stay inside their caps.

    Round-trip fees and adverse slippage are included in the modeled stop loss.
    The nominal exposure room is also reduced by a conservative entry-cost
    reserve. This prevents a nominal 1x portfolio from showing slightly above
    100% margin utilization after the entry fee/slippage has reduced equity.
    A real market gap can still exceed the estimate, so this remains a paper
    risk model rather than a guarantee.
    """
    if equity <= 0 or entry_price <= 0 or stop_distance <= 0:
        return PositionSize(0.0, 0.0, 0.0, 0.0, 0.0)

    leverage = max(1.0, max_leverage)
    risk_budget = equity * risk_rate
    round_trip_cost_per_unit = entry_price * 2 * (fee_rate + slippage_rate)
    modeled_loss_per_unit = stop_distance + round_trip_cost_per_unit
    units_by_risk = risk_budget / modeled_loss_per_unit

    # Reserve enough room for the entry fee and adverse entry slippage before
    # allocating the remaining nominal capacity. The leverage multiplier on the
    # fee reserve reflects that a fee reduces equity and therefore the permitted
    # nominal exposure by leverage times that amount.
    entry_cost_factor = 1.0 + leverage * max(0.0, fee_rate) + max(0.0, slippage_rate)
    exposure_cap = (equity * leverage) / entry_cost_factor
    if max_notional is not None:
        exposure_cap = min(
            exposure_cap,
            max(0.0, max_notional) / entry_cost_factor,
        )
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


def margin_required(notional: float, leverage: float) -> float:
    """Return simulated isolated initial margin for a notional exposure."""
    if notional <= 0:
        return 0.0
    return notional / max(1.0, leverage)


def margin_utilization(notional: float, equity: float, leverage: float) -> float:
    """Return the fraction of account equity tied up as simulated initial margin."""
    if equity <= 0:
        return 1.0 if notional > 0 else 0.0
    return margin_required(notional, leverage) / equity


def estimate_liquidation_price(
    entry_price: float,
    direction: int,
    leverage: float,
    maintenance_margin_rate: float = PAPER_MAINTENANCE_MARGIN_RATE,
) -> float | None:
    """Estimate an isolated-margin liquidation threshold for paper simulation.

    The model reserves ``1/leverage`` as initial margin and a small maintenance
    margin buffer. It is intentionally exchange-agnostic and must not be read as
    Bitpanda's exact margin formula. At 1x there is no modeled liquidation.
    """
    if entry_price <= 0 or leverage <= 1 or direction not in {-1, 1}:
        return None
    if not 0 <= maintenance_margin_rate < 1:
        raise ValueError("maintenance_margin_rate must be between 0 and 1")
    adverse_move = max(0.0, (1.0 / leverage) - maintenance_margin_rate)
    if direction > 0:
        return max(0.0, entry_price * (1.0 - adverse_move))
    return entry_price * (1.0 + adverse_move)


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
