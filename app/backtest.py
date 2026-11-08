from __future__ import annotations

import math
from typing import Any

import pandas as pd

from .config import Settings
from .engine import round_units
from .market_data import MarketData, MarketDataError
from .models import STRATEGY
from .risk import drawdown
from .strategies import add_channels, target_notional
from .tax import is_taxable, settle_year

BARS_PER_YEAR = {"1d": 365.0, "4h": 365.0 * 6}


class Backtester:
    """Historical simulation with the same rules, sizing and costs as the engine.

    Fills: candle close plus slippage (the live engine uses the real order
    book instead). Fees on every order. Open positions are sold at the end so
    the result already contains the exit costs.
    """

    def __init__(self, settings: Settings, market: MarketData):
        self.settings = settings
        self.market = market

    def run(self, bars: int | None = None) -> dict[str, Any]:
        selected_bars = min(1_440, bars or self.settings.backtest_bars)
        constraints = self.market.pair_constraints()
        frames: dict[str, pd.DataFrame] = {}
        failures: dict[str, str] = {}
        for pair in self.settings.pairs:
            if pair not in constraints:
                failures[pair] = "not active"
                continue
            try:
                frame = self.market.history(pair, self.settings.candle_interval, selected_bars)
                frames[pair] = add_channels(frame, self.settings)
            except Exception as exc:
                failures[pair] = str(exc)
        if not frames:
            raise MarketDataError("I found no pair available for the backtest.")

        timestamps = sorted(set().union(*(set(frame.index) for frame in frames.values())))
        strategy = self._simulate(frames, constraints, timestamps, apply_tax=True)
        pre_tax = self._simulate(frames, constraints, timestamps, apply_tax=False)
        strategy["pre_tax_final_equity"] = pre_tax["final_equity"]
        strategy["pre_tax_cagr_pct"] = pre_tax["cagr_pct"]
        benchmark = self._benchmark(frames, timestamps)
        return {
            "status": "ok",
            "pairs": sorted(frames),
            "failures": failures,
            "from": pd.Timestamp(timestamps[0]).isoformat(),
            "to": pd.Timestamp(timestamps[-1]).isoformat(),
            "bars": len(timestamps),
            "interval": self.settings.candle_interval,
            "data_source": self.settings.data_source,
            "fee_rate": self.settings.fee_rate,
            "slippage_rate": self.settings.slippage_rate,
            "tax_rate": self.settings.tax_rate,
            "tax_free_limit": self.settings.tax_free_limit,
            "strategies": [strategy],
            "benchmark": benchmark,
        }

    def _years(self, timestamps: list[pd.Timestamp]) -> float:
        return max(len(timestamps) / BARS_PER_YEAR[self.settings.candle_interval], 1e-9)

    def _simulate(self, frames, constraints, timestamps, *, apply_tax: bool) -> dict[str, Any]:
        s = self.settings
        balance = s.starting_capital  # realized balance (cash + cost basis)
        peak = s.starting_capital
        fees = 0.0
        taxes = 0.0
        carryforward = 0.0
        tax_year = pd.Timestamp(timestamps[0]).tz_convert(s.timezone).year
        year_pnls: list[float] = []
        positions: dict[str, dict[str, float]] = {}
        prices: dict[str, float] = {}
        trades = wins = max_positions = invested_steps = 0
        curve: list[dict[str, Any]] = []
        max_dd = 0.0

        def equity() -> float:
            return balance + sum(
                p["units"] * (prices.get(pair, p["entry"]) - p["entry"]) for pair, p in positions.items()
            )

        def cash() -> float:
            return balance - sum(p["units"] * p["entry"] for p in positions.values())

        def sell(pair: str, close: float, timestamp: pd.Timestamp) -> None:
            nonlocal balance, fees, trades, wins
            position = positions.pop(pair)
            price = close * (1 - s.slippage_rate)
            fee = position["units"] * price * s.fee_rate
            gross = position["units"] * (price - position["entry"])
            balance += gross - fee
            fees += fee
            trades += 1
            net = gross - fee - position["entry_fee"]
            wins += int(net > 0)
            held = (timestamp - position["opened"]).total_seconds() / 86_400
            if is_taxable(held, s.tax_holding_days):
                year_pnls.append(net)

        def settle() -> None:
            nonlocal balance, taxes, carryforward
            result = settle_year(
                year_pnls, loss_carryforward=carryforward, rate=s.tax_rate, allowance=s.tax_free_limit
            )
            year_pnls.clear()
            carryforward = result.loss_carryforward
            if apply_tax:
                balance -= result.tax
                taxes += result.tax

        for timestamp in timestamps:
            year = pd.Timestamp(timestamp).tz_convert(s.timezone).year
            if year != tax_year:
                settle()
                tax_year = year
            bars = {pair: frame.loc[timestamp] for pair, frame in frames.items() if timestamp in frame.index}
            for pair, bar in bars.items():
                prices[pair] = float(bar["Close"])

            for pair in list(positions):
                if pair in bars and int(bars[pair]["SIGNAL"]) < 0:
                    sell(pair, float(bars[pair]["Close"]), timestamp)

            candidates = sorted(
                (
                    (float(bar["STRENGTH"]), pair, bar)
                    for pair, bar in bars.items()
                    if int(bar["SIGNAL"]) > 0 and pair not in positions
                ),
                key=lambda item: item[0],
                reverse=True,
            )
            for _, pair, bar in candidates:
                if len(positions) >= s.max_open_positions:
                    break
                constraint = constraints[pair]
                notional = target_notional(
                    equity=equity(),
                    cash=cash(),
                    pair_count=len(s.pairs),
                    min_order_amount=constraint.min_order_amount,
                    max_order_amount=constraint.max_order_amount,
                    fee_rate=s.fee_rate,
                )
                if notional <= 0:
                    continue
                price = float(bar["Close"]) * (1 + s.slippage_rate)
                units = round_units(notional / price, constraint.size_increment)
                if units <= 0 or units * price < constraint.min_order_amount:
                    continue
                fee = units * price * s.fee_rate
                balance -= fee
                fees += fee
                positions[pair] = {"units": units, "entry": price, "entry_fee": fee, "opened": timestamp}

            max_positions = max(max_positions, len(positions))
            invested_steps += int(bool(positions))
            value = equity()
            peak = max(peak, value)
            max_dd = max(max_dd, drawdown(peak, value))
            curve.append({"date": pd.Timestamp(timestamp).isoformat(), "equity": round(value, 4),
                          "drawdown": round(drawdown(peak, value), 6)})

        for pair in list(positions):
            sell(pair, prices[pair], timestamps[-1])
        settle()
        final = balance
        if curve:
            curve[-1]["equity"] = round(final, 4)
        years = self._years(timestamps)
        return {
            "strategy_id": STRATEGY.strategy_id,
            "label": STRATEGY.label,
            "color": STRATEGY.color,
            "final_equity": round(final, 2),
            "total_return_pct": round((final / s.starting_capital - 1) * 100, 2),
            "cagr_pct": round(((max(final, 1e-9) / s.starting_capital) ** (1 / years) - 1) * 100, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "trades": trades,
            "win_rate_pct": round(wins / trades * 100, 1) if trades else 0.0,
            "fees_paid": round(fees, 2),
            "taxes_paid": round(taxes, 2),
            "time_invested_pct": round(invested_steps / max(len(timestamps), 1) * 100, 1),
            "max_positions": max_positions,
            "curve": _downsample(curve),
        }

    def _benchmark(self, frames, timestamps) -> dict[str, Any]:
        s = self.settings
        allocation = s.starting_capital / len(frames)
        holdings: dict[str, float] = {}
        cash = s.starting_capital
        fees = 0.0
        for pair, frame in frames.items():
            entry = float(frame.iloc[0]["Close"]) * (1 + s.slippage_rate)
            units = allocation / (1 + s.fee_rate) / entry
            fee = units * entry * s.fee_rate
            cash -= units * entry + fee
            fees += fee
            holdings[pair] = units
        closes = pd.DataFrame({pair: frame["Close"] for pair, frame in frames.items()}).reindex(timestamps).ffill()
        curve: list[dict[str, Any]] = []
        peak = s.starting_capital
        max_dd = 0.0
        for timestamp, row in closes.iterrows():
            value = cash + sum(units * float(row[pair]) for pair, units in holdings.items() if not math.isnan(row[pair]))
            peak = max(peak, value)
            max_dd = max(max_dd, drawdown(peak, value))
            curve.append({"date": pd.Timestamp(timestamp).isoformat(), "equity": round(value, 4),
                          "drawdown": round(drawdown(peak, value), 6)})
        final = cash
        for pair, units in holdings.items():
            exit_value = units * float(frames[pair].iloc[-1]["Close"]) * (1 - s.slippage_rate)
            fee = exit_value * s.fee_rate
            final += exit_value - fee
            fees += fee
        # held for the whole period: tax-free after the holding period
        held = (pd.Timestamp(timestamps[-1]) - pd.Timestamp(timestamps[0])).total_seconds() / 86_400
        taxes = 0.0
        if is_taxable(held, s.tax_holding_days):
            taxes = settle_year(
                [final - s.starting_capital], loss_carryforward=0.0, rate=s.tax_rate, allowance=s.tax_free_limit
            ).tax
            final -= taxes
        if curve:
            curve[-1]["equity"] = round(final, 4)
        years = self._years(timestamps)
        return {
            "strategy_id": "benchmark",
            "label": "Equal-weight hold",
            "color": "#c7ccd8",
            "final_equity": round(final, 2),
            "total_return_pct": round((final / s.starting_capital - 1) * 100, 2),
            "cagr_pct": round(((max(final, 1e-9) / s.starting_capital) ** (1 / years) - 1) * 100, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "trades": len(frames),
            "win_rate_pct": None,
            "fees_paid": round(fees, 2),
            "taxes_paid": round(taxes, 2),
            "pre_tax_final_equity": round(final + taxes, 2),
            "time_invested_pct": 100.0,
            "max_positions": len(frames),
            "curve": _downsample(curve),
        }


def _downsample(points: list[dict[str, Any]], maximum: int = 500) -> list[dict[str, Any]]:
    if len(points) <= maximum:
        return points
    step = math.ceil(len(points) / maximum)
    sampled = points[::step]
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled
