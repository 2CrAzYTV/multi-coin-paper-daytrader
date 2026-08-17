from __future__ import annotations

import math
import threading
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from .config import Settings
from .db import Repository
from .market_data import MarketData, MarketDataError
from .models import STRATEGIES, PairConstraint, SignalSnapshot, StrategySpec
from .risk import calculate_position_size, daily_limit_breached, drawdown
from .strategies import (
    add_entry_indicators,
    add_trend_indicators,
    should_exit,
    signal_snapshot,
    stop_distance,
)


class PaperEngine:
    def __init__(self, settings: Settings, repository: Repository, market: MarketData):
        self.settings = settings
        self.repository = repository
        self.market = market
        self._run_lock = threading.Lock()
        self._constraints: dict[str, PairConstraint] = {}
        self._constraints_loaded_at: datetime | None = None
        self._notified_unavailable: set[str] = set()

    @staticmethod
    def _direction(position: dict[str, Any]) -> int:
        return 1 if position["side"] == "long" else -1

    @classmethod
    def mark_equity(
        cls,
        portfolio: dict[str, Any],
        positions: list[dict[str, Any]],
        prices: dict[str, float] | None = None,
    ) -> float:
        equity = float(portfolio["realized_balance"])
        prices = prices or {}
        for position in positions:
            price = float(prices.get(position["pair"], position["last_price"]))
            equity += cls._direction(position) * float(position["units"]) * (
                price - float(position["entry_price"])
            )
        return equity

    def serialize_portfolios(self) -> list[dict[str, Any]]:
        specs = {item.strategy_id: item for item in STRATEGIES}
        result: list[dict[str, Any]] = []
        for portfolio in self.repository.list_portfolios():
            spec = specs[portfolio["strategy_id"]]
            positions = self.repository.list_positions(spec.strategy_id)
            equity = self.mark_equity(portfolio, positions)
            notional = sum(
                abs(float(item["units"]) * float(item["last_price"]))
                for item in positions
            )
            open_risk = sum(float(item["initial_risk"]) for item in positions)
            result.append(
                {
                    **portfolio,
                    "equity": round(equity, 2),
                    "pnl": round(equity - float(portfolio["starting_capital"]), 2),
                    "return_pct": round(
                        (equity / float(portfolio["starting_capital"]) - 1) * 100, 3
                    ),
                    "position_count": len(positions),
                    "position": f"{len(positions)} open" if positions else "Cash",
                    "notional": round(notional, 2),
                    "open_risk": round(open_risk, 2),
                    "effective_leverage": round(notional / equity, 3) if equity > 0 else 0,
                    "max_leverage": spec.max_leverage,
                    "color": spec.color,
                }
            )
        return result

    def serialize_positions(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for position in self.repository.list_positions():
            direction = self._direction(position)
            pnl = direction * float(position["units"]) * (
                float(position["last_price"]) - float(position["entry_price"])
            )
            result.append(
                {
                    **position,
                    "unrealized_pnl": round(pnl, 2),
                    "notional": round(
                        float(position["units"]) * float(position["last_price"]), 2
                    ),
                }
            )
        return result

    def run_once(self) -> dict[str, Any]:
        if not self._run_lock.acquire(blocking=False):
            return {"status": "busy", "message": "I am already running a paper cycle."}
        try:
            constraints = self._load_constraints()
            packages, failures = self._load_market_packages(constraints)
            if not packages:
                raise MarketDataError("I received no market data for any configured pair.")

            new_pairs: set[str] = set()
            for pair, package in packages.items():
                existing = self.repository.get_market(pair)
                if existing is None or pd.Timestamp(
                    package["snapshot"].candle_time
                ) > pd.Timestamp(existing["candle_time"]):
                    new_pairs.add(pair)
            if not new_pairs:
                return {
                    "status": "no_new_candles",
                    "message": "I have already processed every closed 15-minute candle.",
                    "pairs": sorted(packages),
                    "failures": failures,
                }

            now = datetime.now(UTC)
            outcomes = [
                self._process_strategy(spec, packages, new_pairs, now)
                for spec in STRATEGIES
            ]
            for pair in new_pairs:
                self.repository.save_market(
                    packages[pair]["snapshot"], self.settings.data_source
                )
            latest = max(packages[pair]["snapshot"].candle_time for pair in new_pairs)
            self.repository.add_event(
                "info",
                None,
                f"{len(new_pairs)} new market candles processed: {', '.join(sorted(new_pairs))}.",
            )
            return {
                "status": "ok",
                "candle_time": latest,
                "pairs": sorted(packages),
                "new_pairs": sorted(new_pairs),
                "failures": failures,
                "data_source": self.settings.data_source,
                "outcomes": outcomes,
            }
        finally:
            self._run_lock.release()

    def _load_constraints(self) -> dict[str, PairConstraint]:
        now = datetime.now(UTC)
        if (
            not self._constraints
            or self._constraints_loaded_at is None
            or now - self._constraints_loaded_at > timedelta(hours=1)
        ):
            self._constraints = self.market.pair_constraints()
            self._constraints_loaded_at = now
        return self._constraints

    def _load_market_packages(
        self, constraints: dict[str, PairConstraint]
    ) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
        packages: dict[str, dict[str, Any]] = {}
        failures: dict[str, str] = {}
        for pair in self.settings.pairs:
            if pair not in constraints:
                failures[pair] = "Pair is not active on Bitpanda Fusion"
                if pair not in self._notified_unavailable:
                    self.repository.add_event(
                        "warning", None, f"{pair} is skipped because it is not active."
                    )
                    self._notified_unavailable.add(pair)
                continue
            try:
                entry = add_entry_indicators(
                    self.market.history(
                        pair, self.settings.candle_interval, self.settings.history_bars
                    ),
                    self.settings,
                )
                trend = add_trend_indicators(
                    self.market.history(
                        pair, self.settings.trend_interval, self.settings.history_bars
                    ),
                    self.settings,
                )
                snapshot = signal_snapshot(pair, entry, trend)
                packages[pair] = {
                    "entry": entry,
                    "trend": trend,
                    "snapshot": snapshot,
                    "constraint": constraints[pair],
                }
            except Exception as exc:
                failures[pair] = str(exc)
                self.repository.add_event(
                    "error", None, f"I could not load market data for {pair}: {exc}"
                )
        return packages, failures

    def _process_strategy(
        self,
        spec: StrategySpec,
        packages: dict[str, dict[str, Any]],
        new_pairs: set[str],
        now: datetime,
    ) -> dict[str, Any]:
        portfolio = self.repository.get_portfolio(spec.strategy_id)
        prices = {
            pair: float(package["snapshot"].price) for pair, package in packages.items()
        }
        zone = ZoneInfo(self.settings.timezone)
        local_now = now.astimezone(zone)
        today = local_now.date().isoformat()
        events: list[str] = []

        positions = self.repository.list_positions(spec.strategy_id)
        for position in list(positions):
            try:
                opened_date = datetime.fromisoformat(position["opened_at"]).astimezone(zone).date()
            except (TypeError, ValueError):
                opened_date = local_now.date()
            if opened_date < local_now.date() and position["pair"] in prices:
                self._close_position(
                    portfolio,
                    position,
                    prices[position["pair"]],
                    now,
                    "Overnight emergency exit",
                )
                events.append(f"{position['pair']} closed before the trading day")

        positions = self.repository.list_positions(spec.strategy_id)
        if portfolio.get("day_date") != today:
            portfolio["day_date"] = today
            portfolio["day_start_equity"] = self.mark_equity(portfolio, positions, prices)
            portfolio["trades_today"] = 0
            portfolio["daily_locked"] = 0

        session_closed = (local_now.hour, local_now.minute) >= (
            self.settings.session_close_hour,
            self.settings.session_close_minute,
        )

        for position in list(positions):
            pair = position["pair"]
            if pair not in packages:
                continue
            position["last_price"] = prices[pair]
            if pair not in new_pairs:
                self.repository.save_position(position)
                continue
            bar = packages[pair]["entry"].iloc[-1]
            direction = self._direction(position)
            exit_price: float | None = None
            reason = ""
            if direction > 0 and float(bar["Low"]) <= float(position["stop_price"]):
                exit_price = min(float(bar["Open"]), float(position["stop_price"]))
                reason = "Stop-Loss"
            elif direction < 0 and float(bar["High"]) >= float(position["stop_price"]):
                exit_price = max(float(bar["Open"]), float(position["stop_price"]))
                reason = "Stop-Loss"
            elif direction > 0 and float(bar["High"]) >= float(position["take_profit"]):
                exit_price = float(position["take_profit"])
                reason = "Profit target"
            elif direction < 0 and float(bar["Low"]) <= float(position["take_profit"]):
                exit_price = float(position["take_profit"])
                reason = "Profit target"
            elif session_closed:
                exit_price = float(bar["Close"])
                reason = "Daily position close"
            elif should_exit(direction, packages[pair]["entry"]):
                exit_price = float(bar["Close"])
                reason = "EMA exit"

            if exit_price is not None:
                self._close_position(portfolio, position, exit_price, now, reason)
                events.append(f"{pair}: {reason}")
                continue

            risk_per_unit = float(position["initial_risk"]) / max(
                float(position["units"]), 1e-12
            )
            favorable = direction * (
                float(bar["High"] if direction > 0 else bar["Low"])
                - float(position["entry_price"])
            )
            if favorable >= risk_per_unit * self.settings.trailing_trigger_r:
                if direction > 0:
                    position["stop_price"] = max(
                        float(position["stop_price"]), float(position["entry_price"])
                    )
                else:
                    position["stop_price"] = min(
                        float(position["stop_price"]), float(position["entry_price"])
                    )
            self.repository.save_position(position)

        positions = self.repository.list_positions(spec.strategy_id)
        equity = self.mark_equity(portfolio, positions, prices)
        if daily_limit_breached(
            float(portfolio["day_start_equity"]), equity, self.settings.max_daily_loss
        ):
            self._close_all(portfolio, positions, prices, now, "2% daily limit")
            portfolio["daily_locked"] = 1
            events.append("I activated the daily limit")
            self.repository.add_event(
                "warning", spec.strategy_id, f"I activated the 2% daily limit on {today}."
            )

        positions = self.repository.list_positions(spec.strategy_id)
        equity = self.mark_equity(portfolio, positions, prices)
        portfolio["peak_equity"] = max(float(portfolio["peak_equity"]), equity)
        if drawdown(float(portfolio["peak_equity"]), equity) >= self.settings.hard_drawdown:
            self._close_all(portfolio, positions, prices, now, "10% emergency stop")
            portfolio["hard_locked"] = 1
            portfolio["daily_locked"] = 1
            portfolio["lock_reason"] = "I reached the 10% total drawdown limit"
            events.append("I activated the emergency stop")
            self.repository.add_event(
                "error", spec.strategy_id, "I activated the 10% emergency stop and require a reset."
            )

        positions = self.repository.list_positions(spec.strategy_id)
        if not portfolio["hard_locked"] and not portfolio["daily_locked"] and not session_closed:
            candidates = sorted(
                (
                    packages[pair]["snapshot"]
                    for pair in new_pairs
                    if packages[pair]["snapshot"].direction != 0
                ),
                key=lambda item: item.strength,
                reverse=True,
            )
            for candidate in candidates:
                if len(positions) >= self.settings.max_open_positions:
                    break
                if int(portfolio["trades_today"]) >= self.settings.max_trades_per_day:
                    break
                if candidate.direction < 0 and not spec.short_allowed:
                    continue
                if any(position["pair"] == candidate.pair for position in positions):
                    continue
                cooldown = self.repository.get_cooldown(spec.strategy_id, candidate.pair)
                if cooldown and datetime.fromisoformat(cooldown) > now:
                    continue
                opened = self._open_position(
                    portfolio,
                    positions,
                    spec,
                    candidate,
                    packages[candidate.pair]["constraint"],
                    now,
                )
                if opened is not None:
                    positions.append(opened)
                    portfolio["trades_today"] = int(portfolio["trades_today"]) + 1
                    events.append(
                        f"{candidate.pair}: {'Long' if candidate.direction > 0 else 'Short'} opened"
                    )

        positions = self.repository.list_positions(spec.strategy_id)
        equity = self.mark_equity(portfolio, positions, prices)
        portfolio["peak_equity"] = max(float(portfolio["peak_equity"]), equity)
        portfolio["last_run_at"] = now.isoformat(timespec="seconds")
        self.repository.save_portfolio(portfolio)
        captured_at = max(
            packages[pair]["snapshot"].candle_time for pair in new_pairs
        )
        exposure = sum(
            float(position["units"])
            * prices.get(position["pair"], float(position["last_price"]))
            for position in positions
        )
        self.repository.add_snapshot(
            strategy_id=spec.strategy_id,
            captured_at=captured_at,
            equity=equity,
            realized_balance=float(portfolio["realized_balance"]),
            exposure=exposure,
            drawdown_value=drawdown(float(portfolio["peak_equity"]), equity),
        )
        return {
            "strategy_id": spec.strategy_id,
            "status": "processed",
            "equity": round(equity, 2),
            "open_positions": len(positions),
            "trades_today": int(portfolio["trades_today"]),
            "events": events,
        }

    def _open_position(
        self,
        portfolio: dict[str, Any],
        positions: list[dict[str, Any]],
        spec: StrategySpec,
        candidate: SignalSnapshot,
        constraint: PairConstraint,
        now: datetime,
    ) -> dict[str, Any] | None:
        equity = self.mark_equity(portfolio, positions)
        if equity <= 0:
            return None
        aggregate_risk = sum(float(position["initial_risk"]) for position in positions)
        risk_budget = min(
            equity * self.settings.risk_per_trade,
            equity * self.settings.max_aggregate_risk - aggregate_risk,
        )
        total_notional = sum(
            float(position["units"]) * float(position["last_price"])
            for position in positions
        )
        remaining_notional = min(
            equity * spec.max_leverage - total_notional,
            constraint.max_order_amount,
        )
        if risk_budget <= 0 or remaining_notional <= 0:
            return None
        distance = stop_distance(
            price=candidate.price,
            atr=candidate.atr,
            atr_multiple=self.settings.stop_atr_multiple,
            minimum_stop_pct=self.settings.minimum_stop_pct,
        )
        size = calculate_position_size(
            equity=equity,
            entry_price=candidate.price,
            stop_distance=distance,
            risk_rate=risk_budget / equity,
            max_leverage=spec.max_leverage,
            fee_rate=self.settings.fee_rate,
            slippage_rate=self.settings.slippage_rate,
            max_notional=remaining_notional,
        )
        increment = max(constraint.size_increment, 1e-12)
        units = math.floor(size.units / increment) * increment
        notional = units * candidate.price
        if units <= 0 or notional < constraint.min_order_amount:
            self.repository.add_event(
                "info",
                spec.strategy_id,
                f"{candidate.pair} was not opened because its notional is below the minimum.",
            )
            return None
        direction = candidate.direction
        fill = candidate.price * (1 + self.settings.slippage_rate * direction)
        entry_fee = units * fill * self.settings.fee_rate
        stop_price = fill - distance if direction > 0 else fill + distance
        take_profit = (
            fill + distance * self.settings.take_profit_r
            if direction > 0
            else fill - distance * self.settings.take_profit_r
        )
        initial_risk = units * (
            distance + candidate.price * 2 * (self.settings.fee_rate + self.settings.slippage_rate)
        )
        portfolio["realized_balance"] = float(portfolio["realized_balance"]) - entry_fee
        opened_at = now.isoformat(timespec="seconds")
        trade_id = self.repository.open_trade(
            strategy_id=spec.strategy_id,
            pair=candidate.pair,
            opened_at=opened_at,
            side="long" if direction > 0 else "short",
            units=units,
            entry_price=fill,
            stop_price=stop_price,
            take_profit=take_profit,
            initial_risk=initial_risk,
            opened_equity=equity,
            entry_fee=entry_fee,
        )
        position = {
            "strategy_id": spec.strategy_id,
            "pair": candidate.pair,
            "side": "long" if direction > 0 else "short",
            "units": units,
            "entry_price": fill,
            "stop_price": stop_price,
            "take_profit": take_profit,
            "initial_risk": initial_risk,
            "last_price": candidate.price,
            "open_trade_id": trade_id,
            "opened_at": opened_at,
        }
        self.repository.save_position(position)
        self.repository.add_event(
            "info",
            spec.strategy_id,
            (
                f"Paper-{position['side']} {candidate.pair}: {notional:.2f} EUR Nominal, "
                f"modelled risk {initial_risk:.2f} EUR."
            ),
        )
        return position

    def _close_position(
        self,
        portfolio: dict[str, Any],
        position: dict[str, Any],
        market_price: float,
        now: datetime,
        reason: str,
    ) -> None:
        direction = self._direction(position)
        fill = market_price * (1 - self.settings.slippage_rate * direction)
        units = float(position["units"])
        exit_fee = units * fill * self.settings.fee_rate
        gross_pnl = direction * units * (fill - float(position["entry_price"]))
        portfolio["realized_balance"] = (
            float(portfolio["realized_balance"]) + gross_pnl - exit_fee
        )
        trade = self.repository.get_trade(int(position["open_trade_id"]))
        net_pnl = gross_pnl - float(trade["entry_fee"]) - exit_fee
        opened_equity = max(float(trade["opened_equity"]), 1e-12)
        self.repository.close_trade(
            trade_id=int(position["open_trade_id"]),
            closed_at=now.isoformat(timespec="seconds"),
            exit_price=fill,
            exit_fee=exit_fee,
            pnl=net_pnl,
            pnl_pct=net_pnl / opened_equity,
            reason=reason,
        )
        self.repository.delete_position(position["strategy_id"], position["pair"])
        self.repository.set_cooldown(
            position["strategy_id"],
            position["pair"],
            (now + timedelta(minutes=self.settings.cooldown_minutes)).isoformat(
                timespec="seconds"
            ),
        )

    def _close_all(
        self,
        portfolio: dict[str, Any],
        positions: list[dict[str, Any]],
        prices: dict[str, float],
        now: datetime,
        reason: str,
    ) -> None:
        for position in list(positions):
            price = prices.get(position["pair"], float(position["last_price"]))
            self._close_position(portfolio, position, price, now, reason)
