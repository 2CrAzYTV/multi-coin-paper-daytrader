from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Settings
from .models import SignalSnapshot


def _true_range(data: pd.DataFrame) -> pd.Series:
    previous_close = data["Close"].shift(1)
    return pd.concat(
        [
            data["High"] - data["Low"],
            (data["High"] - previous_close).abs(),
            (data["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def _atr(data: pd.DataFrame, window: int) -> pd.Series:
    true_range = _true_range(data)
    return true_range.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def _adx(data: pd.DataFrame, window: int) -> pd.Series:
    """Wilder's ADX: how strongly a market is trending, independent of direction.

    Used as a regime filter on top of the EMA/trend-direction signal - a
    crossover during a directionless chop (low ADX) is far more likely to be
    a whipsaw than the same crossover during a genuine trend.
    """
    up_move = data["High"].diff()
    down_move = -data["Low"].diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    smoothed_tr = _true_range(data).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / window, adjust=False, min_periods=window).mean() / smoothed_tr
    minus_di = 100 * minus_dm.ewm(alpha=1 / window, adjust=False, min_periods=window).mean() / smoothed_tr
    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    return dx.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


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
    data["ADX"] = _adx(data, settings.adx_window)
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    return data


def signal_snapshot(
    pair: str,
    entry_frame: pd.DataFrame,
    trend_frame: pd.DataFrame,
    settings: Settings,
) -> SignalSnapshot:
    if len(entry_frame) < 2 or trend_frame.empty:
        raise ValueError(f"I do not have enough candles for {pair}.")
    previous = entry_frame.iloc[-2]
    current = entry_frame.iloc[-1]
    trend_bar = trend_frame.iloc[-1]
    required = (
        current["EMA_FAST"],
        current["EMA_SLOW"],
        current["ATR"],
        current["RSI"],
        trend_bar["TREND_FAST"],
        trend_bar["TREND_SLOW"],
        trend_bar["ADX"],
    )
    if any(pd.isna(value) for value in required):
        direction, trend, reason = 0, 0, "I do not have enough indicator data yet"
    else:
        cross_up = previous["EMA_FAST"] <= previous["EMA_SLOW"] and current[
            "EMA_FAST"
        ] > current["EMA_SLOW"]
        cross_down = previous["EMA_FAST"] >= previous["EMA_SLOW"] and current[
            "EMA_FAST"
        ] < current["EMA_SLOW"]
        trend = 1 if trend_bar["TREND_FAST"] > trend_bar["TREND_SLOW"] else -1
        trend_strong = float(trend_bar["ADX"]) >= settings.adx_threshold
        volume_median = float(current.get("VOLUME_MEDIAN", 0) or 0)
        volume_ok = volume_median <= 0 or float(current["Volume"]) >= volume_median * 0.8
        rsi = float(current["RSI"])
        if cross_up and trend > 0 and trend_strong and 45 <= rsi <= 70 and volume_ok:
            direction, reason = 1, "Long setup"
        elif cross_down and trend < 0 and trend_strong and 30 <= rsi <= 55 and volume_ok:
            direction, reason = -1, "Short setup"
        elif not volume_ok:
            direction, reason = 0, "Volume filter"
        elif not trend_strong:
            direction, reason = 0, "ADX trend-strength filter"
        else:
            direction, reason = 0, "I found no fresh EMA crossover"
    atr = 0.0 if pd.isna(current.get("ATR")) else float(current["ATR"])
    ema_gap = abs(float(current["EMA_FAST"]) - float(current["EMA_SLOW"]))
    strength = ema_gap / atr if atr > 0 else 0.0
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


def should_exit(direction: int, entry_frame: pd.DataFrame) -> bool:
    latest = entry_frame.iloc[-1]
    if direction > 0:
        return float(latest["EMA_FAST"]) < float(latest["EMA_SLOW"])
    if direction < 0:
        return float(latest["EMA_FAST"]) > float(latest["EMA_SLOW"])
    return False


def stop_distance(
    *, price: float, atr: float, atr_multiple: float, minimum_stop_pct: float
) -> float:
    return max(price * minimum_stop_pct, max(0.0, atr) * atr_multiple)
