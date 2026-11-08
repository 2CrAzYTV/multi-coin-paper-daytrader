from __future__ import annotations


def drawdown(peak_equity: float, current_equity: float) -> float:
    if peak_equity <= 0:
        return 1.0
    return max(0.0, (peak_equity - current_equity) / peak_equity)


def walk_order_book(
    levels: list[tuple[float, float]],
    *,
    notional: float | None = None,
    units: float | None = None,
) -> tuple[float, float] | None:
    """Volume-weighted fill against real order-book levels.

    ``levels`` are (price, quantity) sorted best-first (asks ascending for a
    buy, bids descending for a sell). Pass ``notional`` (EUR to spend) for a
    buy or ``units`` (coins to sell) for a sell. Returns (average_price,
    filled_units) or None when the visible book is too thin.
    """
    if (notional is None) == (units is None):
        raise ValueError("I require exactly one of notional or units.")
    spent = 0.0
    filled = 0.0
    for price, quantity in levels:
        if price <= 0 or quantity <= 0:
            continue
        if notional is not None:
            take = min(quantity, (notional - spent) / price)
        else:
            take = min(quantity, units - filled)
        spent += take * price
        filled += take
        done = (notional is not None and spent >= notional * 0.999999) or (
            units is not None and filled >= units * 0.999999
        )
        if done:
            return spent / filled, filled
    return None
