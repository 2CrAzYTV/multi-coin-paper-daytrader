from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from .config import Settings
from .market_data import MarketData, MarketDataError
from .models import STRATEGIES, PairConstraint, StrategySpec
from .risk import (
    calculate_position_size,
    daily_limit_breached,
    drawdown,
    estimate_liquidation_price,
    margin_utilization,
)
from .strategies import add_entry_indicators, add_trend_indicators, stop_distance


@dataclass
class SimAccount:
    balance: float
    peak: float
    day_date: str = ""
    day_start: float = 0.0
    daily_locked: bool = False
    hard_locked: bool = False
    trades_today: int = 0
    positions: dict[str, dict[str, float | int | str]] = field(default_factory=dict)
    cooldowns: dict[str, pd.Timestamp] = field(default_factory=dict)
    trades: int = 0
    wins: int = 0
    liquidations: int = 0
    daily_limit_hits: int = 0
    max_positions: int = 0
    max_open_risk: float = 0.0
    max_effective_leverage: float = 0.0
    max_margin_utilization: float = 0.0
    margin_utilization_sum: float = 0.0
    margin_utilization_samples: int = 0
    trade_pnls: list[float] = field(default_factory=list)
    long_trade_pnls: list[float] = field(default_factory=list)
    short_trade_pnls: list[float] = field(default_factory=list)
    curve: list[dict[str, Any]] = field(default_factory=list)


class Backtester:
    """Portfolio backtest across every configured coin and shared risk caps."""

    def __init__(self, settings: Settings, market: MarketData):
        self.settings = settings
        self.market = market

    def run(self, bars: int | None = None) -> dict[str, Any]:
        selected_bars = min(1_000, bars or self.settings.backtest_bars)
        constraints = self.market.pair_constraints()
        frames: dict[str, pd.DataFrame] = {}
        failures: dict[str, str] = {}
        for pair in self.settings.pairs:
            if pair not in constraints:
                failures[pair] = "not active"
                continue
            try:
                frame = self.market.history(pair, self.settings.candle_interval, selected_bars)
                frames[pair] = self._prepare(frame)
            except Exception as exc:
                failures[pair] = str(exc)
        if not frames:
            raise MarketDataError("I found no pair available for the multi-coin backtest.")

        timestamps = sorted(set().union(*(set(frame.index) for frame in frames.values())))
        results = [self._run_strategy(spec, frames, constraints, timestamps) for spec in STRATEGIES]
        benchmark = self._benchmark(frames, timestamps)
        return {
            "status": "ok",
            "pairs": sorted(frames),
            "failures": failures,
            "from": pd.Timestamp(timestamps[0]).isoformat(),
            "to": pd.Timestamp(timestamps[-1]).isoformat(),
            "bars": len(timestamps),
            "data_source": self.settings.data_source,
            "strategies": results,
            "benchmark": benchmark,
            "liquidation_model": "paper-isolated-margin-estimate",
        }

    def _prepare(self, frame: pd.DataFrame) -> pd.DataFrame:
        entry = add_entry_indicators(frame, self.settings)
        hourly = frame.resample("1h", label="right", closed="right").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        ).dropna()
        trend = add_trend_indicators(hourly, self.settings)
        entry["TREND_FAST"] = trend["TREND_FAST"].reindex(entry.index, method="ffill")
        entry["TREND_SLOW"] = trend["TREND_SLOW"].reindex(entry.index, method="ffill")
        previous_fast = entry["EMA_FAST"].shift(1)
        previous_slow = entry["EMA_SLOW"].shift(1)
        volume_ok = entry["Volume"] >= entry["VOLUME_MEDIAN"].fillna(0) * 0.8
        long_setup = (
            (previous_fast <= previous_slow)
            & (entry["EMA_FAST"] > entry["EMA_SLOW"])
            & (entry["TREND_FAST"] > entry["TREND_SLOW"])
            & entry["RSI"].between(45, 70)
            & volume_ok
        )
        short_setup = (
            (previous_fast >= previous_slow)
            & (entry["EMA_FAST"] < entry["EMA_SLOW"])
            & (entry["TREND_FAST"] < entry["TREND_SLOW"])
            & entry["RSI"].between(30, 55)
            & volume_ok
        )
        entry["SIGNAL"] = 0
        entry.loc[long_setup, "SIGNAL"] = 1
        entry.loc[short_setup, "SIGNAL"] = -1
        return entry

    def _run_strategy(
        self,
        spec: StrategySpec,
        frames: dict[str, pd.DataFrame],
        constraints: dict[str, PairConstraint],
        timestamps: list[pd.Timestamp],
    ) -> dict[str, Any]:
        account = SimAccount(
            balance=self.settings.starting_capital,
            peak=self.settings.starting_capital,
            day_start=self.settings.starting_capital,
        )
        prices: dict[str, float] = {}
        zone = ZoneInfo(self.settings.timezone)
        for step, timestamp in enumerate(timestamps):
            bars = {pair: frame.loc[timestamp] for pair, frame in frames.items() if timestamp in frame.index}
            for pair, bar in bars.items():
                prices[pair] = float(bar["Close"])
            local = pd.Timestamp(timestamp).tz_convert(zone)
            date_value = local.date().isoformat()

            if account.day_date and account.day_date != date_value:
                self._close_all(account, prices, float(self.settings.slippage_rate))
            if account.day_date != date_value:
                account.day_date = date_value
                account.day_start = self._equity(account, prices)
                account.daily_locked = False
                account.trades_today = 0

            session_closed = (local.hour, local.minute) >= (
                self.settings.session_close_hour,
                self.settings.session_close_minute,
            )
            for pair, position in list(account.positions.items()):
                if pair not in bars:
                    continue
                bar = bars[pair]
                direction = int(position["direction"])
                liquidation_price = estimate_liquidation_price(
                    float(position["entry"]), direction, spec.max_leverage
                )
                exit_price: float | None = None
                liquidated = False
                if liquidation_price is not None and direction > 0 and float(bar["Open"]) <= liquidation_price:
                    exit_price = float(bar["Open"])
                    liquidated = True
                elif liquidation_price is not None and direction < 0 and float(bar["Open"]) >= liquidation_price:
                    exit_price = float(bar["Open"])
                    liquidated = True
                elif direction > 0 and float(bar["Low"]) <= float(position["stop"]):
                    exit_price = min(float(bar["Open"]), float(position["stop"]))
                elif direction < 0 and float(bar["High"]) >= float(position["stop"]):
                    exit_price = max(float(bar["Open"]), float(position["stop"]))
                elif direction > 0 and float(bar["High"]) >= float(position["target"]):
                    exit_price = float(position["target"])
                elif direction < 0 and float(bar["Low"]) <= float(position["target"]):
                    exit_price = float(position["target"])
                elif session_closed:
                    exit_price = float(bar["Close"])
                elif direction > 0 and float(bar["EMA_FAST"]) < float(bar["EMA_SLOW"]):
                    exit_price = float(bar["Close"])
                elif direction < 0 and float(bar["EMA_FAST"]) > float(bar["EMA_SLOW"]):
                    exit_price = float(bar["Close"])
                if exit_price is not None:
                    won = self._close(account, pair, exit_price)
                    account.trades += 1
                    account.wins += int(won)
                    account.liquidations += int(liquidated)
                    account.cooldowns[pair] = timestamp + pd.Timedelta(minutes=self.settings.cooldown_minutes)
                    continue
                risk_per_unit = float(position["initial_risk"]) / max(float(position["units"]), 1e-12)
                favorable = direction * (
                    float(bar["High"] if direction > 0 else bar["Low"]) - float(position["entry"])
                )
                if favorable >= risk_per_unit * self.settings.trailing_trigger_r:
                    if direction > 0:
                        position["stop"] = max(float(position["stop"]), float(position["entry"]))
                    else:
                        position["stop"] = min(float(position["stop"]), float(position["entry"]))

            equity = self._equity(account, prices)
            if daily_limit_breached(account.day_start, equity, self.settings.max_daily_loss):
                self._close_all(account, prices, self.settings.slippage_rate)
                account.daily_locked = True
                account.daily_limit_hits += 1
                equity = self._equity(account, prices)
            account.peak = max(account.peak, equity)
            if drawdown(account.peak, equity) >= self.settings.hard_drawdown:
                self._close_all(account, prices, self.settings.slippage_rate)
                account.hard_locked = True
                account.daily_locked = True

            if not account.daily_locked and not account.hard_locked and not session_closed:
                candidates: list[tuple[float, str, int, pd.Series]] = []
                for pair, bar in bars.items():
                    signal = int(bar["SIGNAL"])
                    if not signal or (signal < 0 and not spec.short_allowed):
                        continue
                    atr = float(bar["ATR"])
                    strength = (
                        abs(float(bar["EMA_FAST"]) - float(bar["EMA_SLOW"])) / atr
                        if atr > 0 and math.isfinite(atr)
                        else 0.0
                    )
                    candidates.append((strength, pair, signal, bar))
                candidates.sort(reverse=True)
                for _, pair, direction, bar in candidates:
                    if len(account.positions) >= self.settings.max_open_positions:
                        break
                    if account.trades_today >= self.settings.max_trades_per_day:
                        break
                    if pair in account.positions or account.cooldowns.get(pair, timestamp) > timestamp:
                        continue
                    self._open(account, spec, pair, direction, bar, constraints[pair], prices)

            equity = self._equity(account, prices)
            account.peak = max(account.peak, equity)
            exposure = sum(
                float(item["units"]) * prices.get(name, float(item["entry"]))
                for name, item in account.positions.items()
            )
            if equity > 0:
                account.max_effective_leverage = max(account.max_effective_leverage, exposure / equity)
                utilization = margin_utilization(exposure, equity, spec.max_leverage)
                account.max_margin_utilization = max(account.max_margin_utilization, utilization)
                if exposure > 0:
                    account.margin_utilization_sum += utilization
                    account.margin_utilization_samples += 1
            if step % 4 == 0 or step == len(timestamps) - 1:
                account.curve.append(
                    {
                        "date": pd.Timestamp(timestamp).isoformat(),
                        "equity": round(equity, 4),
                        "drawdown": round(drawdown(account.peak, equity), 6),
                    }
                )

        self._close_all(account, prices, self.settings.slippage_rate)
        final_equity = account.balance
        if account.curve:
            account.curve[-1]["equity"] = round(final_equity, 4)
        diagnostics = _trade_diagnostics(account)
        return {
            "strategy_id": spec.strategy_id,
            "label": spec.label,
            "color": spec.color,
            "max_leverage": spec.max_leverage,
            "final_equity": round(final_equity, 2),
            "total_return_pct": round((final_equity / self.settings.starting_capital - 1) * 100, 2),
            "max_drawdown_pct": round(
                max((point["drawdown"] for point in account.curve), default=0) * 100, 2
            ),
            "trades": account.trades,
            "win_rate_pct": round(account.wins / account.trades * 100, 1) if account.trades else 0.0,
            "liquidations": account.liquidations,
            "daily_limit_hits": account.daily_limit_hits,
            "max_positions": account.max_positions,
            "max_open_risk": round(account.max_open_risk, 2),
            "max_effective_leverage": round(account.max_effective_leverage, 3),
            "max_margin_utilization_pct": round(account.max_margin_utilization * 100, 2),
            "avg_margin_utilization_pct": round(
                account.margin_utilization_sum / account.margin_utilization_samples * 100, 2
            ) if account.margin_utilization_samples else 0.0,
            **diagnostics,
            "hard_locked": account.hard_locked,
            "curve": _downsample(account.curve),
        }

    def _open(
        self,
        account: SimAccount,
        spec: StrategySpec,
        pair: str,
        direction: int,
        bar: pd.Series,
        constraint: PairConstraint,
        prices: dict[str, float],
    ) -> None:
        equity = self._equity(account, prices)
        aggregate_risk = sum(float(item["initial_risk"]) for item in account.positions.values())
        risk_budget = min(
            equity * self.settings.risk_per_trade,
            equity * self.settings.max_aggregate_risk - aggregate_risk,
        )
        exposure = sum(
            float(item["units"]) * prices.get(name, float(item["entry"]))
            for name, item in account.positions.items()
        )
        remaining = min(equity * spec.max_leverage - exposure, constraint.max_order_amount)
        price = float(bar["Close"])
        distance = stop_distance(
            price=price,
            atr=float(bar["ATR"]),
            atr_multiple=self.settings.stop_atr_multiple,
            minimum_stop_pct=self.settings.minimum_stop_pct,
        )
        if risk_budget <= 0 or remaining <= 0 or not math.isfinite(distance):
            return
        size = calculate_position_size(
            equity=equity,
            entry_price=price,
            stop_distance=distance,
            risk_rate=risk_budget / equity,
            max_leverage=spec.max_leverage,
            fee_rate=self.settings.fee_rate,
            slippage_rate=self.settings.slippage_rate,
            max_notional=remaining,
        )
        increment = max(constraint.size_increment, 1e-12)
        units = math.floor(size.units / increment) * increment
        if units <= 0 or units * price < constraint.min_order_amount:
            return
        fill = price * (1 + self.settings.slippage_rate * direction)
        entry_fee = units * fill * self.settings.fee_rate
        account.balance -= entry_fee
        initial_risk = units * (
            distance + price * 2 * (self.settings.fee_rate + self.settings.slippage_rate)
        )
        account.positions[pair] = {
            "direction": direction,
            "units": units,
            "entry": fill,
            "stop": fill - distance if direction > 0 else fill + distance,
            "target": fill + direction * distance * self.settings.take_profit_r,
            "entry_fee": entry_fee,
            "initial_risk": initial_risk,
        }
        account.trades_today += 1
        account.max_positions = max(account.max_positions, len(account.positions))
        account.max_open_risk = max(
            account.max_open_risk,
            sum(float(item["initial_risk"]) for item in account.positions.values()),
        )

    def _close(self, account: SimAccount, pair: str, market_price: float) -> bool:
        position = account.positions.pop(pair)
        direction = int(position["direction"])
        fill = market_price * (1 - self.settings.slippage_rate * direction)
        units = float(position["units"])
        exit_fee = units * fill * self.settings.fee_rate
        gross = direction * units * (fill - float(position["entry"]))
        net = gross - float(position["entry_fee"]) - exit_fee
        account.balance += gross - exit_fee
        account.trade_pnls.append(net)
        (account.long_trade_pnls if direction > 0 else account.short_trade_pnls).append(net)
        return net > 0

    def _close_all(self, account: SimAccount, prices: dict[str, float], slippage: float) -> None:
        del slippage
        for pair in list(account.positions):
            if pair in prices:
                won = self._close(account, pair, prices[pair])
                account.trades += 1
                account.wins += int(won)

    @staticmethod
    def _equity(account: SimAccount, prices: dict[str, float]) -> float:
        equity = account.balance
        for pair, position in account.positions.items():
            price = prices.get(pair, float(position["entry"]))
            equity += int(position["direction"]) * float(position["units"]) * (
                price - float(position["entry"])
            )
        return equity

    def _benchmark(
        self, frames: dict[str, pd.DataFrame], timestamps: list[pd.Timestamp]
    ) -> dict[str, Any]:
        allocation = self.settings.starting_capital / len(frames)
        holdings: dict[str, tuple[float, float]] = {}
        cash = self.settings.starting_capital
        for pair, frame in frames.items():
            entry = float(frame.iloc[0]["Close"]) * (1 + self.settings.slippage_rate)
            budget = allocation / (1 + self.settings.fee_rate)
            units = budget / entry
            fee = units * entry * self.settings.fee_rate
            cash -= units * entry + fee
            holdings[pair] = (units, entry)
        curve: list[dict[str, Any]] = []
        peak = self.settings.starting_capital
        for step, timestamp in enumerate(timestamps):
            if step % 4 and step != len(timestamps) - 1:
                continue
            value = cash
            for pair, (units, entry) in holdings.items():
                frame = frames[pair]
                available = frame.loc[:timestamp]
                price = float(available.iloc[-1]["Close"]) if not available.empty else entry
                value += units * price
            peak = max(peak, value)
            curve.append(
                {
                    "date": pd.Timestamp(timestamp).isoformat(),
                    "equity": round(value, 4),
                    "drawdown": round(drawdown(peak, value), 6),
                }
            )
        final_value = cash
        for pair, (units, _) in holdings.items():
            exit_price = float(frames[pair].iloc[-1]["Close"]) * (1 - self.settings.slippage_rate)
            final_value += units * exit_price * (1 - self.settings.fee_rate)
        if curve:
            curve[-1]["equity"] = round(final_value, 4)
        return {
            "strategy_id": "benchmark",
            "label": "Equal-weight hold",
            "color": "#c7ccd8",
            "max_leverage": 1.0,
            "final_equity": round(final_value, 2),
            "total_return_pct": round((final_value / self.settings.starting_capital - 1) * 100, 2),
            "max_drawdown_pct": round(
                max((point["drawdown"] for point in curve), default=0) * 100, 2
            ),
            "trades": len(frames),
            "win_rate_pct": None,
            "liquidations": None,
            "daily_limit_hits": None,
            "max_positions": len(frames),
            "max_open_risk": None,
            "max_effective_leverage": 1.0,
            "max_margin_utilization_pct": None,
            "avg_margin_utilization_pct": None,
            "profit_factor": None,
            "expectancy_eur": None,
            "average_win_eur": None,
            "average_loss_eur": None,
            "largest_loss_eur": None,
            "long_trades": None,
            "long_win_rate_pct": None,
            "long_pnl_eur": None,
            "short_trades": None,
            "short_win_rate_pct": None,
            "short_pnl_eur": None,
            "hard_locked": False,
            "curve": _downsample(curve),
        }


def _trade_diagnostics(account: SimAccount) -> dict[str, Any]:
    wins = [value for value in account.trade_pnls if value > 0]
    losses = [value for value in account.trade_pnls if value <= 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (None if gross_profit == 0 else 999.0)

    def side_stats(values: list[float]) -> tuple[int, float, float]:
        count = len(values)
        winners = sum(1 for value in values if value > 0)
        return count, (winners / count * 100 if count else 0.0), sum(values)

    long_count, long_win_rate, long_pnl = side_stats(account.long_trade_pnls)
    short_count, short_win_rate, short_pnl = side_stats(account.short_trade_pnls)
    return {
        "profit_factor": round(profit_factor, 3) if profit_factor is not None else None,
        "expectancy_eur": round(sum(account.trade_pnls) / len(account.trade_pnls), 3)
        if account.trade_pnls else 0.0,
        "average_win_eur": round(gross_profit / len(wins), 3) if wins else 0.0,
        "average_loss_eur": round(sum(losses) / len(losses), 3) if losses else 0.0,
        "largest_loss_eur": round(min(losses), 3) if losses else 0.0,
        "long_trades": long_count,
        "long_win_rate_pct": round(long_win_rate, 1),
        "long_pnl_eur": round(long_pnl, 2),
        "short_trades": short_count,
        "short_win_rate_pct": round(short_win_rate, 1),
        "short_pnl_eur": round(short_pnl, 2),
    }


def _downsample(points: list[dict[str, Any]], maximum: int = 500) -> list[dict[str, Any]]:
    if len(points) <= maximum:
        return points
    step = math.ceil(len(points) / maximum)
    sampled = points[::step]
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled
