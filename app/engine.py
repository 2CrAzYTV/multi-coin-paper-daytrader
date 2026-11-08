from __future__ import annotations

import math
import threading
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd

from .config import Settings
from .db import Repository
from .market_data import MarketData, MarketDataError
from .models import STRATEGY, Fill, PairConstraint, SignalSnapshot
from .risk import drawdown
from .strategies import signal_snapshot, target_notional


def round_units(units: float, increment: float) -> float:
    step = max(increment, 1e-12)
    return math.floor(units / step + 1e-9) * step


class PaperEngine:
    """Live paper simulation: one spot account, long only, no leverage.

    Signals are evaluated once per closed candle (daily by default). Fills are
    priced from the live Fusion order book (read-only) when available, else
    from the candle close plus the configured slippage. Fees are charged on
    every simulated order.
    """

    def __init__(self, settings: Settings, repository: Repository, market: MarketData):
        self.settings = settings
        self.repository = repository
        self.market = market
        self._run_lock = threading.Lock()
        self._constraints: dict[str, PairConstraint] = {}
        self._constraints_loaded_at: datetime | None = None
        self._notified_unavailable: set[str] = set()

    # -- accounting ---------------------------------------------------------

    @staticmethod
    def equity(
        portfolio: dict[str, Any],
        positions: list[dict[str, Any]],
        prices: dict[str, float] | None = None,
    ) -> float:
        prices = prices or {}
        value = float(portfolio["realized_balance"])
        for position in positions:
            price = float(prices.get(position["pair"], position["last_price"]))
            value += float(position["units"]) * (price - float(position["entry_price"]))
        return value

    @staticmethod
    def cash(portfolio: dict[str, Any], positions: list[dict[str, Any]]) -> float:
        return float(portfolio["realized_balance"]) - sum(
            float(position["units"]) * float(position["entry_price"]) for position in positions
        )

    def serialize_portfolios(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for portfolio in self.repository.list_portfolios():
            positions = self.repository.list_positions(portfolio["strategy_id"])
            equity = self.equity(portfolio, positions)
            exposure = sum(float(p["units"]) * float(p["last_price"]) for p in positions)
            start = float(portfolio["starting_capital"])
            result.append(
                {
                    **portfolio,
                    **self.repository.trade_stats(portfolio["strategy_id"]),
                    "label": STRATEGY.label,
                    "color": STRATEGY.color,
                    "equity": round(equity, 2),
                    "pnl": round(equity - start, 2),
                    "return_pct": round((equity / start - 1) * 100, 3),
                    "cash": round(self.cash(portfolio, positions), 2),
                    "exposure": round(exposure, 2),
                    "position_count": len(positions),
                    "drawdown_pct": round(
                        drawdown(max(float(portfolio["peak_equity"]), equity), equity) * 100, 2
                    ),
                }
            )
        return result

    def serialize_positions(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for position in self.repository.list_positions():
            units = float(position["units"])
            entry = float(position["entry_price"])
            last = float(position["last_price"])
            result.append(
                {
                    **position,
                    "notional": round(units * last, 2),
                    "unrealized_pnl": round(units * (last - entry), 2),
                    "unrealized_pct": round((last / entry - 1) * 100, 2) if entry > 0 else 0.0,
                }
            )
        return result

    # -- cycle --------------------------------------------------------------

    def run_once(self) -> dict[str, Any]:
        if not self._run_lock.acquire(blocking=False):
            return {"status": "busy", "message": "I am already running a paper cycle."}
        try:
            constraints = self._load_constraints()
            snapshots, failures = self._load_snapshots(constraints)
            if not snapshots:
                raise MarketDataError("I received no market data for any configured pair.")

            new_pairs = set()
            for pair, snapshot in snapshots.items():
                stored = self.repository.get_market(pair)
                if stored is None or pd.Timestamp(snapshot.candle_time) > pd.Timestamp(
                    stored["candle_time"]
                ):
                    new_pairs.add(pair)
            if not new_pairs:
                self._mark_to_market()
                return {
                    "status": "no_new_candles",
                    "message": "I have already processed every closed candle.",
                    "pairs": sorted(snapshots),
                    "failures": failures,
                }

            now = datetime.now(UTC)
            events = self._process(snapshots, constraints, new_pairs, now)
            for pair in new_pairs:
                self.repository.save_market(snapshots[pair], self.settings.data_source)
            latest = max(snapshots[pair].candle_time for pair in new_pairs)
            self.repository.add_event(
                "info",
                None,
                f"{len(new_pairs)} new market candles processed: {', '.join(sorted(new_pairs))}.",
            )
            return {
                "status": "ok",
                "candle_time": latest,
                "pairs": sorted(snapshots),
                "new_pairs": sorted(new_pairs),
                "failures": failures,
                "data_source": self.settings.data_source,
                "events": events,
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

    def _load_snapshots(
        self, constraints: dict[str, PairConstraint]
    ) -> tuple[dict[str, SignalSnapshot], dict[str, str]]:
        snapshots: dict[str, SignalSnapshot] = {}
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
                frame = self.market.history(
                    pair, self.settings.candle_interval, self.settings.history_bars
                )
                snapshots[pair] = signal_snapshot(pair, frame, self.settings)
            except Exception as exc:
                failures[pair] = str(exc)
                self.repository.add_event(
                    "error", None, f"I could not load market data for {pair}: {exc}"
                )
        return snapshots, failures

    def _mark_to_market(self) -> None:
        for position in self.repository.list_positions(STRATEGY.strategy_id):
            mid = self.market.mid_price(position["pair"])
            if mid:
                position["last_price"] = mid
                self.repository.save_position(position)

    def _fill(self, pair: str, side: str, close: float, *, notional=None, units=None) -> Fill:
        fill = self.market.order_book_fill(pair, side, notional=notional, units=units)
        if fill is not None:
            return fill
        direction = 1 if side == "buy" else -1
        price = close * (1 + self.settings.slippage_rate * direction)
        return Fill(price=price, units=units if units is not None else notional / price, source="candle")

    def _process(
        self,
        snapshots: dict[str, SignalSnapshot],
        constraints: dict[str, PairConstraint],
        new_pairs: set[str],
        now: datetime,
    ) -> list[str]:
        portfolio = self.repository.get_portfolio(STRATEGY.strategy_id)
        events: list[str] = []
        prices = {pair: snapshot.price for pair, snapshot in snapshots.items()}

        # 1. exits first, so the freed cash is available for new entries
        for position in self.repository.list_positions(STRATEGY.strategy_id):
            pair = position["pair"]
            if pair not in new_pairs:
                continue
            snapshot = snapshots[pair]
            if snapshot.direction < 0:
                self._sell(portfolio, position, snapshot, now, "Exit channel broken")
                events.append(f"{pair}: sold")
            else:
                position["last_price"] = snapshot.price
                position["exit_level"] = snapshot.exit_level
                self.repository.save_position(position)

        # 2. entries, strongest breakout first
        positions = self.repository.list_positions(STRATEGY.strategy_id)
        held = {position["pair"] for position in positions}
        candidates = sorted(
            (
                snapshots[pair]
                for pair in new_pairs
                if snapshots[pair].direction > 0 and pair not in held
            ),
            key=lambda item: item.strength,
            reverse=True,
        )
        for candidate in candidates:
            if len(positions) >= self.settings.max_open_positions:
                break
            constraint = constraints[candidate.pair]
            notional = target_notional(
                equity=self.equity(portfolio, positions, prices),
                cash=self.cash(portfolio, positions),
                pair_count=len(self.settings.pairs),
                min_order_amount=constraint.min_order_amount,
                max_order_amount=constraint.max_order_amount,
                fee_rate=self.settings.fee_rate,
            )
            if notional <= 0:
                self.repository.add_event(
                    "info",
                    STRATEGY.strategy_id,
                    f"{candidate.pair} signal skipped: not enough cash for the minimum order.",
                )
                continue
            position = self._buy(portfolio, candidate, constraint, notional, now)
            if position is not None:
                positions.append(position)
                events.append(f"{candidate.pair}: bought")

        positions = self.repository.list_positions(STRATEGY.strategy_id)
        equity = self.equity(portfolio, positions, prices)
        portfolio["peak_equity"] = max(float(portfolio["peak_equity"]), equity)
        portfolio["last_run_at"] = now.isoformat(timespec="seconds")
        self.repository.save_portfolio(portfolio)
        self.repository.add_snapshot(
            strategy_id=STRATEGY.strategy_id,
            captured_at=max(snapshots[pair].candle_time for pair in new_pairs),
            equity=equity,
            cash=self.cash(portfolio, positions),
            exposure=sum(float(p["units"]) * prices.get(p["pair"], float(p["last_price"])) for p in positions),
            drawdown_value=drawdown(float(portfolio["peak_equity"]), equity),
        )
        return events

    def _buy(
        self,
        portfolio: dict[str, Any],
        snapshot: SignalSnapshot,
        constraint: PairConstraint,
        notional: float,
        now: datetime,
    ) -> dict[str, Any] | None:
        fill = self._fill(snapshot.pair, "buy", snapshot.price, notional=notional)
        units = round_units(fill.units, constraint.size_increment)
        if units <= 0 or units * fill.price < constraint.min_order_amount:
            return None
        fee = units * fill.price * self.settings.fee_rate
        portfolio["realized_balance"] = float(portfolio["realized_balance"]) - fee
        portfolio["fees_paid"] = float(portfolio["fees_paid"]) + fee
        opened_at = now.isoformat(timespec="seconds")
        trade_id = self.repository.open_trade(
            strategy_id=STRATEGY.strategy_id,
            pair=snapshot.pair,
            opened_at=opened_at,
            units=units,
            entry_price=fill.price,
            entry_fee=fee,
            fill_source=fill.source,
        )
        position = {
            "strategy_id": STRATEGY.strategy_id,
            "pair": snapshot.pair,
            "units": units,
            "entry_price": fill.price,
            "exit_level": snapshot.exit_level,
            "last_price": snapshot.price,
            "open_trade_id": trade_id,
            "opened_at": opened_at,
        }
        self.repository.save_position(position)
        self.repository.add_event(
            "info",
            STRATEGY.strategy_id,
            f"Paper buy {snapshot.pair}: {units * fill.price:.2f} EUR at {fill.price:.6g} "
            f"(fee {fee:.2f} EUR, {fill.source}).",
        )
        return position

    def _sell(
        self,
        portfolio: dict[str, Any],
        position: dict[str, Any],
        snapshot: SignalSnapshot,
        now: datetime,
        reason: str,
    ) -> None:
        units = float(position["units"])
        fill = self._fill(position["pair"], "sell", snapshot.price, units=units)
        fee = units * fill.price * self.settings.fee_rate
        gross = units * (fill.price - float(position["entry_price"]))
        portfolio["realized_balance"] = float(portfolio["realized_balance"]) + gross - fee
        portfolio["fees_paid"] = float(portfolio["fees_paid"]) + fee
        trade = self.repository.get_trade(int(position["open_trade_id"]))
        net = gross - float(trade["entry_fee"]) - fee
        cost_basis = max(units * float(position["entry_price"]), 1e-12)
        self.repository.close_trade(
            trade_id=int(position["open_trade_id"]),
            closed_at=now.isoformat(timespec="seconds"),
            exit_price=fill.price,
            exit_fee=fee,
            fill_source=fill.source,
            pnl=net,
            pnl_pct=net / cost_basis,
            reason=reason,
        )
        self.repository.delete_position(position["strategy_id"], position["pair"])
        self.repository.add_event(
            "info",
            STRATEGY.strategy_id,
            f"Paper sell {position['pair']}: {net:+.2f} EUR after fees ({fill.source}).",
        )
