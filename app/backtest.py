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
from .strategies import (
    add_entry_indicators,
    add_signal_columns,
    add_trend_indicators,
    should_exit,
    stop_distance,
)


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
    pair_trade_pnls: dict[str, list[float]] = field(default_factory=dict)
    pair_long_trade_pnls: dict[str, list[float]] = field(default_factory=dict)
    pair_short_trade_pnls: dict[str, list[float]] = field(default_factory=dict)
    curve: list[dict[str, Any]] = field(default_factory=list)


class Backtester:
    """Portfolio backtest across every configured coin and shared risk caps."""

    def __init__(self, settings: Settings, market: MarketData):
        self.settings = settings
        self.market = market

    def run(self, bars: int | None = None) -> dict[str, Any]:
        selected_bars = min(5_000, bars or self.settings.backtest_bars)
        # Fusion can be one candle short at a window boundary. Requiring 95% keeps
        # genuinely new/empty markets out without rejecting otherwise complete history.
        minimum_history_bars = max(100, math.floor(selected_bars * 0.95))
        constraints = self.market.pair_constraints()
        frames: dict[str, pd.DataFrame] = {}
        failures: dict[str, str] = {}
        skipped: dict[str, str] = {}
        for pair in self.settings.pairs:
            if pair not in constraints:
                skipped[pair] = "not active on Bitpanda Fusion"
                continue
            try:
                frame = self.market.history(pair, self.settings.candle_interval, selected_bars)
                if len(frame) < minimum_history_bars:
                    skipped[pair] = (
                        f"insufficient history: {len(frame)} candles; "
                        f"minimum {minimum_history_bars}"
                    )
                    continue
                if frame.index.has_duplicates:
                    skipped[pair] = "duplicate candle timestamps"
                    continue
                if frame[["Open", "High", "Low", "Close"]].isna().any().any():
                    skipped[pair] = "missing OHLC values"
                    continue
                frames[pair] = self._prepare(frame)
            except Exception as exc:
                skipped[pair] = f"market data unavailable: {exc}"
        if not frames:
            raise MarketDataError("I found no pair with enough quality history for the multi-coin backtest.")

        timestamps = sorted(set().union(*(set(frame.index) for frame in frames.values())))
        results = [self._run_strategy(spec, frames, constraints, timestamps) for spec in STRATEGIES]
        benchmark = self._benchmark(frames, timestamps)
        return {
            "status": "ok",
            "pairs": sorted(frames),
            "failures": failures,
            "skipped_pairs": skipped,
            "quality_filter": {
                "requested_bars": selected_bars,
                "minimum_history_bars": minimum_history_bars,
                "usable_count": len(frames),
                "skipped_count": len(skipped),
            },
            "from": pd.Timestamp(timestamps[0]).isoformat(),
            "to": pd.Timestamp(timestamps[-1]).isoformat(),
            "bars": len(timestamps),
            "data_source": self.settings.data_source,
            "strategies": results,
            "benchmark": benchmark,
            "liquidation_model": "paper-isolated-margin-estimate",
            "signal_model": "quality-filtered-ema-trend-v2",
        }

    def _prepare(self, frame: pd.DataFrame) -> pd.DataFrame:
        entry = add_entry_indicators(frame, self.settings)
        hourly = frame.resample("1h", label="right", closed="right").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        ).dropna()
        trend = add_trend_indicators(hourly, self.settings)
        return add_signal_columns(entry, trend, self.settings)

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
                elif should_exit(
                    direction,
                    frames[pair].loc[:timestamp],
                    self.settings.exit_confirmation_bars,
                ):
                    exit_price = float(bar["Close"])
                if exit_price is not None:
                    won = self._close(account, pair, exit_price)
                    account.trades += 1
                    account.wins += int(won)
                    account.liquidations += int(liquidated)
                    account.cooldowns[pair] = timestamp + pd.Timedelta(minutes=self.settings.cooldown_minutes)
                    continue
                risk_per_unit = float(position["initial_risk"]) / max(float(position["units"]), 1e-12)
                if direction > 0:
                    position["stop"] = max(float(position["stop"]), float(bar["Close"]) - risk_per_unit)
                else:
                    position["stop"] = min(float(position["stop"]), float(bar["Close"]) + risk_per_unit)

            equity = self._equity(account, prices)
            account.peak = max(account.peak, equity)
            if drawdown(account.peak, equity) >= self.settings.max_drawdown:
                self._close_all(account, prices, float(self.settings.slippage_rate))
                account.hard_locked = True
            if daily_limit_breached(account.day_start, equity, self.settings.daily_loss_limit):
                self._close_all(account, prices, float(self.settings.slippage_rate))
                if not account.daily_locked:
                    account.daily_limit_hits += 1
                account.daily_locked = True

            if not account.hard_locked and not account.daily_locked and not session_closed:
                for pair, bar in bars.items():
                    if pair in account.positions or len(account.positions) >= self.settings.max_positions:
                        continue
                    cooldown = account.cooldowns.get(pair)
                    if cooldown is not None and timestamp < cooldown:
                        continue
                    direction = int(bar["Signal"])
                    if direction == 0 or (direction < 0 and not spec.allow_short):
                        continue
                    price = float(bar["Close"])
                    stop = stop_distance(bar, self.settings)
                    if not math.isfinite(stop) or stop <= 0:
                        continue
                    current_equity = self._equity(account, prices)
                    open_risk = sum(float(item["initial_risk"]) for item in account.positions.values())
                    sizing = calculate_position_size(
                        equity=current_equity,
                        price=price,
                        stop_distance=stop,
                        risk_fraction=self.settings.risk_per_trade,
                        leverage=spec.max_leverage,
                        current_open_risk=open_risk,
                        max_open_risk_fraction=self.settings.max_open_risk,
                    )
                    constraint = constraints[pair]
                    units = sizing.units
                    notional = units * price
                    if notional < constraint.min_order_value:
                        continue
                    if constraint.max_order_value is not None and notional > constraint.max_order_value:
                        units = constraint.max_order_value / price
                        notional = units * price
                    if constraint.amount_step is not None and constraint.amount_step > 0:
                        units = math.floor(units / constraint.amount_step) * constraint.amount_step
                        notional = units * price
                    if units <= 0 or notional < constraint.min_order_value:
                        continue
                    target = price + direction * stop * self.settings.reward_risk
                    account.positions[pair] = {
                        "direction": direction,
                        "entry": price,
                        "units": units,
                        "stop": price - direction * stop,
                        "target": target,
                        "initial_risk": units * stop,
                    }
                    account.trades_today += 1
                    account.max_positions = max(account.max_positions, len(account.positions))

            equity = self._equity(account, prices)
            notional = sum(abs(float(item["units"]) * prices.get(pair, float(item["entry"]))) for pair, item in account.positions.items())
            open_risk = sum(float(item["initial_risk"]) for item in account.positions.values())
            effective_leverage = notional / equity if equity > 0 else 0.0
            utilization = margin_utilization(notional, equity, spec.max_leverage)
            account.max_open_risk = max(account.max_open_risk, open_risk)
            account.max_effective_leverage = max(account.max_effective_leverage, effective_leverage)
            account.max_margin_utilization = max(account.max_margin_utilization, utilization)
            account.margin_utilization_sum += utilization
            account.margin_utilization_samples += 1
            if step % 4 == 0 or step == len(timestamps) - 1:
                account.curve.append({"time": pd.Timestamp(timestamp).isoformat(), "equity": round(equity, 2)})

        self._close_all(account, prices, float(self.settings.slippage_rate))
        final_equity = account.balance
        return self._serialize(spec, account, final_equity)

    def _close(self, account: SimAccount, pair: str, price: float) -> bool:
        position = account.positions.pop(pair)
        direction = int(position["direction"])
        entry = float(position["entry"])
        units = float(position["units"])
        fee = (entry + price) * units * self.settings.fee_rate
        pnl = direction * units * (price - entry) - fee
        account.balance += pnl
        account.trade_pnls.append(pnl)
        account.pair_trade_pnls.setdefault(pair, []).append(pnl)
        if direction > 0:
            account.long_trade_pnls.append(pnl)
            account.pair_long_trade_pnls.setdefault(pair, []).append(pnl)
        else:
            account.short_trade_pnls.append(pnl)
            account.pair_short_trade_pnls.setdefault(pair, []).append(pnl)
        return pnl > 0

    def _close_all(self, account: SimAccount, prices: dict[str, float], slippage: float) -> None:
        for pair, position in list(account.positions.items()):
            price = prices.get(pair, float(position["entry"]))
            direction = int(position["direction"])
            execution = price * (1 - slippage) if direction > 0 else price * (1 + slippage)
            won = self._close(account, pair, execution)
            account.trades += 1
            account.wins += int(won)

    @staticmethod
    def _equity(account: SimAccount, prices: dict[str, float]) -> float:
        equity = account.balance
        for pair, position in account.positions.items():
            direction = int(position["direction"])
            equity += direction * float(position["units"]) * (
                prices.get(pair, float(position["entry"])) - float(position["entry"])
            )
        return equity

    def _serialize(self, spec: StrategySpec, account: SimAccount, equity: float) -> dict[str, Any]:
        losses = [value for value in account.trade_pnls if value < 0]
        gains = [value for value in account.trade_pnls if value > 0]
        pair_stats = []
        for pair in sorted(account.pair_trade_pnls):
            pnls = account.pair_trade_pnls[pair]
            long_pnls = account.pair_long_trade_pnls.get(pair, [])
            short_pnls = account.pair_short_trade_pnls.get(pair, [])
            pair_stats.append(
                {
                    "pair": pair,
                    "trades": len(pnls),
                    "wins": sum(value > 0 for value in pnls),
                    "win_rate_pct": round(sum(value > 0 for value in pnls) / len(pnls) * 100, 2),
                    "pnl": round(sum(pnls), 2),
                    "avg_pnl": round(sum(pnls) / len(pnls), 2),
                    "long_trades": len(long_pnls),
                    "long_pnl": round(sum(long_pnls), 2),
                    "short_trades": len(short_pnls),
                    "short_pnl": round(sum(short_pnls), 2),
                }
            )
        pair_stats.sort(key=lambda item: (item["pnl"], item["trades"]), reverse=True)
        return {
            "id": spec.strategy_id,
            "name": spec.name,
            "color": spec.color,
            "equity": round(equity, 2),
            "return_pct": round((equity / self.settings.starting_capital - 1) * 100, 3),
            "max_drawdown_pct": round(self._max_drawdown(account.curve) * 100, 3),
            "trades": account.trades,
            "wins": account.wins,
            "win_rate_pct": round(account.wins / account.trades * 100, 2) if account.trades else 0,
            "liquidations": account.liquidations,
            "daily_limit_hits": account.daily_limit_hits,
            "max_positions": account.max_positions,
            "max_open_risk": round(account.max_open_risk, 2),
            "max_effective_leverage": round(account.max_effective_leverage, 3),
            "max_margin_utilization_pct": round(account.max_margin_utilization * 100, 2),
            "avg_margin_utilization_pct": round(account.margin_utilization_sum / account.margin_utilization_samples * 100, 2) if account.margin_utilization_samples else 0,
            "profit_factor": round(sum(gains) / abs(sum(losses)), 3) if losses else (None if gains else 0),
            "expectancy": round(sum(account.trade_pnls) / account.trades, 2) if account.trades else 0,
            "avg_win": round(sum(gains) / len(gains), 2) if gains else 0,
            "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0,
            "largest_loss": round(min(losses), 2) if losses else 0,
            "long_trades": len(account.long_trade_pnls),
            "long_wins": sum(value > 0 for value in account.long_trade_pnls),
            "long_pnl": round(sum(account.long_trade_pnls), 2),
            "short_trades": len(account.short_trade_pnls),
            "short_wins": sum(value > 0 for value in account.short_trade_pnls),
            "short_pnl": round(sum(account.short_trade_pnls), 2),
            "pair_stats": pair_stats,
            "curve": account.curve,
        }

    @staticmethod
    def _max_drawdown(curve: list[dict[str, Any]]) -> float:
        peak = 0.0
        worst = 0.0
        for point in curve:
            equity = float(point["equity"])
            peak = max(peak, equity)
            if peak > 0:
                worst = max(worst, (peak - equity) / peak)
        return worst

    def _benchmark(self, frames: dict[str, pd.DataFrame], timestamps: list[pd.Timestamp]) -> dict[str, Any]:
        allocations = self.settings.starting_capital / len(frames)
        units: dict[str, float] = {}
        for pair, frame in frames.items():
            units[pair] = allocations / float(frame.iloc[0]["Close"])
        curve: list[dict[str, Any]] = []
        for timestamp in timestamps:
            equity = 0.0
            for pair, frame in frames.items():
                history = frame.loc[:timestamp]
                if history.empty:
                    equity += allocations
                else:
                    equity += units[pair] * float(history.iloc[-1]["Close"])
            curve.append({"time": pd.Timestamp(timestamp).isoformat(), "equity": round(equity, 2)})
        equity = curve[-1]["equity"]
        return {
            "id": "benchmark",
            "name": "Gleichgewichtet halten",
            "color": "#c4cad5",
            "equity": equity,
            "return_pct": round((equity / self.settings.starting_capital - 1) * 100, 3),
            "max_drawdown_pct": round(self._max_drawdown(curve) * 100, 3),
            "trades": len(frames),
            "wins": None,
            "win_rate_pct": None,
            "liquidations": None,
            "daily_limit_hits": None,
            "max_positions": len(frames),
            "max_open_risk": None,
            "max_effective_leverage": 1,
            "max_margin_utilization_pct": None,
            "avg_margin_utilization_pct": None,
            "profit_factor": None,
            "expectancy": None,
            "avg_win": None,
            "avg_loss": None,
            "largest_loss": None,
            "long_trades": None,
            "long_wins": None,
            "long_pnl": None,
            "short_trades": None,
            "short_wins": None,
            "short_pnl": None,
            "pair_stats": [],
            "curve": curve,
        }
