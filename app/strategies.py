"""Donchian channel trend following (classic "Turtle System 2" rules).

Long only, spot, no leverage:

- buy when a candle CLOSES above the highest high of the previous
  ``entry_window`` candles (default 55)
- sell when a candle CLOSES below the lowest low of the previous
  ``exit_window`` candles (default 20)

Both channels exclude the current candle, so a decision never uses
information that was not known when the candle closed.

Why this and not an intraday strategy: with Bitpanda Fusion's 0.25% fee per
order (plus spread/slippage) a round trip costs about 0.6%. Every intraday
variant tested on one year of real 15-minute Fusion data lost money after
costs, while this rule trades only a few times per coin and year.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Settings
from .models import SignalSnapshot


def _atr(data: pd.DataFrame, window: int) -> pd.Series:
    previous_close = data["Close"].shift(1)
    true_range = pd.concat(
        [
            data["High"] - data["Low"],
            (data["High"] - previous_close).abs(),
            (data["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def add_channels(frame: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    data = frame.copy()
    data["ENTRY_LEVEL"] = (
        data["High"].rolling(settings.entry_window, min_periods=settings.entry_window).max().shift(1)
    )
    data["EXIT_LEVEL"] = (
        data["Low"].rolling(settings.exit_window, min_periods=settings.exit_window).min().shift(1)
    )
    data["ATR"] = _atr(data, settings.atr_window)
    close = data["Close"]
    data["SIGNAL"] = 0
    data.loc[close > data["ENTRY_LEVEL"], "SIGNAL"] = 1
    data.loc[close < data["EXIT_LEVEL"], "SIGNAL"] = -1
    # Breakout strength in ATRs, used to rank simultaneous buy signals.
    data["STRENGTH"] = ((close - data["ENTRY_LEVEL"]) / data["ATR"]).where(
        data["SIGNAL"] > 0, 0.0
    )
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    data["STRENGTH"] = data["STRENGTH"].fillna(0.0)
    return data


def signal_snapshot(pair: str, frame: pd.DataFrame, settings: Settings) -> SignalSnapshot:
    data = add_channels(frame, settings)
    if len(data) < settings.entry_window + 1:
        raise ValueError(f"I do not have enough candles for {pair}.")
    current = data.iloc[-1]
    entry_level = current["ENTRY_LEVEL"]
    exit_level = current["EXIT_LEVEL"]
    if pd.isna(entry_level) or pd.isna(exit_level):
        direction, reason = 0, "I do not have enough candles yet"
    else:
        direction = int(current["SIGNAL"])
        if direction > 0:
            reason = "Breakout above the entry channel"
        elif direction < 0:
            reason = "Close below the exit channel"
        else:
            reason = "Inside the channel"
    return SignalSnapshot(
        pair=pair,
        candle_time=pd.Timestamp(data.index[-1]).isoformat(),
        price=float(current["Close"]),
        atr=0.0 if pd.isna(current["ATR"]) else float(current["ATR"]),
        entry_level=0.0 if pd.isna(entry_level) else float(entry_level),
        exit_level=0.0 if pd.isna(exit_level) else float(exit_level),
        direction=direction,
        strength=float(current["STRENGTH"]),
        reason=reason,
    )


def target_notional(
    *,
    equity: float,
    cash: float,
    pair_count: int,
    min_order_amount: float,
    max_order_amount: float,
    fee_rate: float,
) -> float:
    """Equal share of equity per coin, limited by available cash (spot, no margin).

    If the equal share is below the exchange minimum but the cash allows the
    minimum order, the minimum is used - that is what a person with a small
    account would do. Returns 0 when the order is impossible.
    """
    if equity <= 0 or cash <= 0:
        return 0.0
    # 1% buffer so unit rounding and a slightly different fill price cannot
    # push the order below the exchange minimum.
    minimum = min_order_amount * 1.01
    affordable = cash / (1 + fee_rate)
    share = max(equity / max(pair_count, 1), minimum)
    notional = min(share, affordable, max_order_amount)
    return notional if notional >= minimum else 0.0
