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


# --- Opening Range Breakout (ORB) -------------------------------------------
#
# Crypto trades 24/7, so the "opening" is a configurable daily session start
# (default 15:30 Europe/Berlin = US cash open, when crypto volume picks up).
# The first ORB_RANGE_MINUTES define the range. Inside the entry window, the
# first candle that CLOSES above the range high (long) or below the range low
# (short) is the signal - at most one long and one short attempt per day.
# The stop sits at the range midpoint, so the risk is defined by the range
# itself rather than by ATR.

ORB_COLUMNS = ("ORB_HIGH", "ORB_LOW", "ORB_SIGNAL", "ORB_STOP", "ORB_STRENGTH", "ORB_REASON")


def add_orb_columns(
    entry: pd.DataFrame,
    settings: Settings,
    trend_up: pd.Series | None = None,
) -> pd.DataFrame:
    """Add vectorised ORB columns to a frame that already has ATR/VOLUME_MEDIAN.

    The index holds candle OPEN times. ``trend_up`` (bool, aligned to the
    index) is only used when ``settings.orb_trend_filter`` is enabled; it must
    contain information that was known when each candle closed.
    """
    from .config import INTERVAL_MINUTES

    data = entry.copy()
    candle_minutes = INTERVAL_MINUTES[settings.candle_interval]
    local = data.index.tz_convert(settings.timezone)
    day = pd.Series(local.date, index=data.index)
    minute_of_day = pd.Series(local.hour * 60 + local.minute, index=data.index)
    start = settings.orb_session_hour * 60 + settings.orb_session_minute
    range_end = start + settings.orb_range_minutes
    window_end = range_end + settings.orb_entry_window_minutes

    in_range = (minute_of_day >= start) & (minute_of_day + candle_minutes <= range_end)
    in_window = (minute_of_day >= range_end) & (minute_of_day < window_end)
    expected = settings.orb_range_minutes // candle_minutes

    range_high = data["High"].where(in_range).groupby(day).transform("max")
    range_low = data["Low"].where(in_range).groupby(day).transform("min")
    range_count = in_range.groupby(day).transform("sum")
    complete = range_count >= expected
    range_high = range_high.where(complete & in_window)
    range_low = range_low.where(complete & in_window)

    close = data["Close"]
    above = in_window & complete & (close > range_high)
    below = in_window & complete & (close < range_low)
    first_above = above & (above.astype(int).groupby(day).cumsum() == 1)
    first_below = below & (below.astype(int).groupby(day).cumsum() == 1)

    atr = data["ATR"]
    width = range_high - range_low
    range_ok = atr.notna() & (atr > 0) & (width <= atr * settings.orb_max_range_atr)
    median = data["VOLUME_MEDIAN"]
    volume_ok = median.isna() | (median <= 0) | (data["Volume"] >= median)
    if settings.orb_trend_filter and trend_up is not None:
        trend_long = trend_up.reindex(data.index).fillna(False).astype(bool)
        trend_short = ~trend_long & trend_up.reindex(data.index).notna()
    else:
        trend_long = pd.Series(True, index=data.index)
        trend_short = pd.Series(True, index=data.index)

    long_ok = first_above & range_ok & volume_ok & trend_long
    short_ok = first_below & range_ok & volume_ok & trend_short
    mid = (range_high + range_low) / 2
    minimum = close * settings.minimum_stop_pct

    data["ORB_HIGH"] = range_high
    data["ORB_LOW"] = range_low
    data["ORB_SIGNAL"] = 0
    data.loc[long_ok, "ORB_SIGNAL"] = 1
    data.loc[short_ok, "ORB_SIGNAL"] = -1
    stop = pd.Series(np.nan, index=data.index)
    stop[long_ok] = np.maximum(close - mid, minimum)[long_ok]
    stop[short_ok] = np.maximum(mid - close, minimum)[short_ok]
    data["ORB_STOP"] = stop
    safe_atr = atr.where(atr > 0)
    strength = pd.Series(0.0, index=data.index)
    strength[long_ok] = ((close - range_high) / safe_atr)[long_ok]
    strength[short_ok] = ((range_low - close) / safe_atr)[short_ok]
    data["ORB_STRENGTH"] = strength.fillna(0.0)

    reason = pd.Series("Outside the ORB entry window", index=data.index, dtype=object)
    reason[in_range] = "Building the ORB opening range"
    reason[in_window & ~complete] = "ORB range incomplete"
    reason[in_window & complete] = "No ORB breakout"
    reason[(first_above | first_below) & ~range_ok] = "ORB range too wide"
    reason[(first_above | first_below) & range_ok & ~volume_ok] = "Volume filter"
    reason[
        ((first_above & ~trend_long) | (first_below & ~trend_short)) & range_ok & volume_ok
    ] = "ORB trend filter"
    reason[in_window & complete & (above | below) & ~(first_above | first_below)] = (
        "ORB breakout already used today"
    )
    reason[long_ok] = "ORB long breakout"
    reason[short_ok] = "ORB short breakout"
    data["ORB_REASON"] = reason
    return data


def orb_snapshot(
    pair: str,
    entry_frame: pd.DataFrame,
    trend_frame: pd.DataFrame,
    settings: Settings,
) -> SignalSnapshot:
    """Live ORB decision for the latest closed candle."""
    if len(entry_frame) < 2:
        raise ValueError(f"I do not have enough candles for {pair}.")
    trend_up = None
    if not trend_frame.empty:
        bar = trend_frame.iloc[-1]
        if not pd.isna(bar.get("TREND_FAST")) and not pd.isna(bar.get("TREND_SLOW")):
            trend_up = pd.Series(
                bool(bar["TREND_FAST"] > bar["TREND_SLOW"]), index=entry_frame.index
            )
    data = add_orb_columns(entry_frame, settings, trend_up)
    current = data.iloc[-1]
    atr = 0.0 if pd.isna(current.get("ATR")) else float(current["ATR"])
    direction = int(current["ORB_SIGNAL"])
    stop = current["ORB_STOP"]
    return SignalSnapshot(
        pair=pair,
        candle_time=pd.Timestamp(data.index[-1]).isoformat(),
        price=float(current["Close"]),
        atr=atr,
        rsi=float(current.get("RSI", 50.0)),
        direction=direction,
        trend=0 if trend_up is None else (1 if bool(trend_up.iloc[-1]) else -1),
        strength=float(current["ORB_STRENGTH"]),
        reason=str(current["ORB_REASON"]),
        stop_distance=None if pd.isna(stop) else float(stop),
    )
