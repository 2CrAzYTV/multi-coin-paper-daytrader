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


def _rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    loss = (-delta.clip(upper=0)).ewm(
        alpha=1 / window, adjust=False, min_periods=window
    ).mean()
    relative_strength = gain / loss.replace(0, np.nan)
    result = 100 - (100 / (1 + relative_strength))
    return result.fillna(50.0)


def add_entry_indicators(frame: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    data = frame.copy()
    data["EMA_FAST"] = data["Close"].ewm(
        span=settings.fast_window, adjust=False
    ).mean()
    data["EMA_SLOW"] = data["Close"].ewm(
        span=settings.slow_window, adjust=False
    ).mean()
    data["ATR"] = _atr(data, settings.atr_window)
    data["RSI"] = _rsi(data["Close"], settings.rsi_window)
    data["VOLUME_MEDIAN"] = data["Volume"].rolling(20, min_periods=10).median()
    data["EMA_STRENGTH"] = (
        (data["EMA_FAST"] - data["EMA_SLOW"]).abs()
        / data["ATR"].replace(0, np.nan)
    )
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    return data


def add_trend_indicators(frame: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    data = frame.copy()
    data["TREND_FAST"] = data["Close"].ewm(
        span=settings.trend_fast_window, adjust=False
    ).mean()
    data["TREND_SLOW"] = data["Close"].ewm(
        span=settings.trend_slow_window, adjust=False
    ).mean()
    data["TREND_STRENGTH_PCT"] = (
        (data["TREND_FAST"] - data["TREND_SLOW"]).abs()
        / data["Close"].replace(0, np.nan)
    )
    data["TREND_FAST_SLOPE"] = data["TREND_FAST"].diff(2)
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    return data


def add_signal_columns(
    entry_frame: pd.DataFrame,
    trend_frame: pd.DataFrame,
    settings: Settings,
) -> pd.DataFrame:
    """Attach the same entry rules used by both live paper trading and backtests."""
    data = entry_frame.copy()
    for column in (
        "TREND_FAST",
        "TREND_SLOW",
        "TREND_STRENGTH_PCT",
        "TREND_FAST_SLOPE",
    ):
        data[column] = trend_frame[column].reindex(data.index, method="ffill")

    previous_fast = data["EMA_FAST"].shift(1)
    previous_slow = data["EMA_SLOW"].shift(1)
    cross_up = (previous_fast <= previous_slow) & (data["EMA_FAST"] > data["EMA_SLOW"])
    cross_down = (previous_fast >= previous_slow) & (data["EMA_FAST"] < data["EMA_SLOW"])
    volume_ok = (
        data["VOLUME_MEDIAN"].isna()
        | (data["VOLUME_MEDIAN"] <= 0)
        | (data["Volume"] >= data["VOLUME_MEDIAN"] * settings.volume_multiplier)
    )
    strength_ok = data["EMA_STRENGTH"].fillna(0) >= settings.signal_min_strength
    trend_strength_ok = (
        data["TREND_STRENGTH_PCT"].fillna(0) >= settings.trend_min_strength_pct
    )
    long_trend = (
        (data["TREND_FAST"] > data["TREND_SLOW"])
        & (data["TREND_FAST_SLOPE"] > 0)
        & trend_strength_ok
    )
    short_trend = (
        (data["TREND_FAST"] < data["TREND_SLOW"])
        & (data["TREND_FAST_SLOPE"] < 0)
        & trend_strength_ok
    )
    long_confirmation = (data["Close"] > data["EMA_FAST"]) & data["RSI"].between(
        settings.long_rsi_min, settings.long_rsi_max
    )
    short_confirmation = (data["Close"] < data["EMA_FAST"]) & data["RSI"].between(
        settings.short_rsi_min, settings.short_rsi_max
    )

    data["SIGNAL"] = 0
    data.loc[
        cross_up & long_trend & long_confirmation & volume_ok & strength_ok,
        "SIGNAL",
    ] = 1
    data.loc[
        cross_down & short_trend & short_confirmation & volume_ok & strength_ok,
        "SIGNAL",
    ] = -1
    return data


def signal_snapshot(
    pair: str,
    entry_frame: pd.DataFrame,
    trend_frame: pd.DataFrame,
    settings: Settings | None = None,
) -> SignalSnapshot:
    if len(entry_frame) < 2 or trend_frame.empty:
        raise ValueError(f"I do not have enough candles for {pair}.")
    settings = settings or Settings.from_env()
    prepared = add_signal_columns(entry_frame, trend_frame, settings)
    current = prepared.iloc[-1]
    required = (
        current["EMA_FAST"],
        current["EMA_SLOW"],
        current["ATR"],
        current["RSI"],
        current["TREND_FAST"],
        current["TREND_SLOW"],
        current["TREND_STRENGTH_PCT"],
        current["TREND_FAST_SLOPE"],
    )
    if any(pd.isna(value) for value in required):
        direction, trend, reason = 0, 0, "I do not have enough indicator data yet"
    else:
        direction = int(current["SIGNAL"])
        trend = 1 if current["TREND_FAST"] > current["TREND_SLOW"] else -1
        if direction > 0:
            reason = "Long setup: crossover + momentum + confirmed uptrend"
        elif direction < 0:
            reason = "Short setup: crossover + momentum + confirmed downtrend"
        elif float(current.get("EMA_STRENGTH", 0) or 0) < settings.signal_min_strength:
            reason = "Signal strength filter"
        elif float(current.get("TREND_STRENGTH_PCT", 0) or 0) < settings.trend_min_strength_pct:
            reason = "Trend strength filter"
        else:
            reason = "I found no high-quality fresh EMA crossover"
    atr = 0.0 if pd.isna(current.get("ATR")) else float(current["ATR"])
    strength = 0.0 if pd.isna(current.get("EMA_STRENGTH")) else float(current["EMA_STRENGTH"])
    return SignalSnapshot(
        pair=pair,
        candle_time=pd.Timestamp(entry_frame.index[-1]).isoformat(),
        price=float(current["Close"]),
        atr=atr,
        rsi=float(current.get("RSI", 50.0)),
        direction=direction,
        trend=trend,
        strength=strength,
        reason=reason,
    )


def should_exit(
    direction: int,
    entry_frame: pd.DataFrame,
    confirmation_bars: int | None = None,
) -> bool:
    bars = Settings.from_env().exit_confirmation_bars if confirmation_bars is None else confirmation_bars
    bars = max(1, int(bars))
    if len(entry_frame) < bars:
        return False
    recent = entry_frame.iloc[-bars:]
    if direction > 0:
        return bool((recent["EMA_FAST"] < recent["EMA_SLOW"]).all())
    if direction < 0:
        return bool((recent["EMA_FAST"] > recent["EMA_SLOW"]).all())
    return False


def stop_distance(
    *, price: float, atr: float, atr_multiple: float, minimum_stop_pct: float
) -> float:
    return max(price * minimum_stop_pct, max(0.0, atr) * atr_multiple)
