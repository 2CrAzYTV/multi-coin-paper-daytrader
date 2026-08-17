from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import STRATEGIES, SignalSnapshot


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Repository:
    """SQLite persistence for the v2 multi-asset paper simulator.

    The ``dt_`` prefix keeps upgrades isolated from the older daily-swing
    schema if a user already started version 0.1.
    """

    def __init__(self, database_path: Path, starting_capital: float):
        self.database_path = database_path
        self.starting_capital = starting_capital
        self._lock = threading.RLock()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=20)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS dt_portfolios (
            strategy_id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            starting_capital REAL NOT NULL,
            realized_balance REAL NOT NULL,
            peak_equity REAL NOT NULL,
            hard_locked INTEGER NOT NULL DEFAULT 0,
            lock_reason TEXT NOT NULL DEFAULT '',
            daily_locked INTEGER NOT NULL DEFAULT 0,
            day_date TEXT,
            day_start_equity REAL NOT NULL,
            trades_today INTEGER NOT NULL DEFAULT 0,
            last_run_at TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dt_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            pair TEXT NOT NULL,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            side TEXT NOT NULL,
            units REAL NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            stop_price REAL NOT NULL,
            take_profit REAL NOT NULL,
            initial_risk REAL NOT NULL,
            opened_equity REAL NOT NULL,
            entry_fee REAL NOT NULL DEFAULT 0,
            exit_fee REAL NOT NULL DEFAULT 0,
            pnl REAL,
            pnl_pct REAL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            FOREIGN KEY (strategy_id) REFERENCES dt_portfolios(strategy_id)
        );

        CREATE TABLE IF NOT EXISTS dt_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            pair TEXT NOT NULL,
            side TEXT NOT NULL,
            units REAL NOT NULL,
            entry_price REAL NOT NULL,
            stop_price REAL NOT NULL,
            take_profit REAL NOT NULL,
            initial_risk REAL NOT NULL,
            last_price REAL NOT NULL,
            open_trade_id INTEGER NOT NULL,
            opened_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(strategy_id, pair),
            FOREIGN KEY (strategy_id) REFERENCES dt_portfolios(strategy_id),
            FOREIGN KEY (open_trade_id) REFERENCES dt_trades(id)
        );

        CREATE TABLE IF NOT EXISTS dt_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            equity REAL NOT NULL,
            realized_balance REAL NOT NULL,
            exposure REAL NOT NULL,
            drawdown REAL NOT NULL,
            UNIQUE(strategy_id, captured_at),
            FOREIGN KEY (strategy_id) REFERENCES dt_portfolios(strategy_id)
        );

        CREATE TABLE IF NOT EXISTS dt_markets (
            pair TEXT PRIMARY KEY,
            candle_time TEXT NOT NULL,
            price REAL NOT NULL,
            signal INTEGER NOT NULL,
            trend INTEGER NOT NULL,
            rsi REAL NOT NULL,
            reason TEXT NOT NULL,
            source TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dt_cooldowns (
            strategy_id TEXT NOT NULL,
            pair TEXT NOT NULL,
            until_at TEXT NOT NULL,
            PRIMARY KEY(strategy_id, pair),
            FOREIGN KEY (strategy_id) REFERENCES dt_portfolios(strategy_id)
        );

        CREATE TABLE IF NOT EXISTS dt_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            level TEXT NOT NULL,
            strategy_id TEXT,
            message TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_dt_trades_strategy
            ON dt_trades(strategy_id, id DESC);
        CREATE INDEX IF NOT EXISTS idx_dt_positions_strategy
            ON dt_positions(strategy_id, pair);
        CREATE INDEX IF NOT EXISTS idx_dt_snapshots_strategy
            ON dt_snapshots(strategy_id, captured_at);
        """
        with self._lock, self._connect() as connection:
            connection.executescript(schema)
            now = utc_now()
            for strategy in STRATEGIES:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO dt_portfolios (
                        strategy_id, label, starting_capital, realized_balance,
                        peak_equity, day_start_equity, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        strategy.strategy_id,
                        strategy.label,
                        self.starting_capital,
                        self.starting_capital,
                        self.starting_capital,
                        self.starting_capital,
                        now,
                    ),
                )

    def reset(self) -> None:
        tables = (
            "dt_cooldowns",
            "dt_positions",
            "dt_snapshots",
            "dt_trades",
            "dt_markets",
            "dt_events",
            "dt_portfolios",
        )
        with self._lock, self._connect() as connection:
            for table in tables:
                connection.execute(f"DELETE FROM {table}")
        self.initialize()
        self.add_event("warning", None, "Multi-Coin-Paper-Konten wurden zurueckgesetzt.")

    def get_portfolio(self, strategy_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM dt_portfolios WHERE strategy_id = ?", (strategy_id,)
            ).fetchone()
        if row is None:
            raise KeyError(strategy_id)
        return dict(row)

    def list_portfolios(self) -> list[dict[str, Any]]:
        order = {strategy.strategy_id: index for index, strategy in enumerate(STRATEGIES)}
        with self._connect() as connection:
            rows = [dict(row) for row in connection.execute("SELECT * FROM dt_portfolios")]
        return sorted(rows, key=lambda item: order.get(item["strategy_id"], 999))

    def save_portfolio(self, portfolio: dict[str, Any]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE dt_portfolios SET
                    realized_balance = ?, peak_equity = ?, hard_locked = ?,
                    lock_reason = ?, daily_locked = ?, day_date = ?,
                    day_start_equity = ?, trades_today = ?, last_run_at = ?,
                    updated_at = ?
                WHERE strategy_id = ?
                """,
                (
                    portfolio["realized_balance"],
                    portfolio["peak_equity"],
                    int(bool(portfolio["hard_locked"])),
                    portfolio.get("lock_reason", ""),
                    int(bool(portfolio.get("daily_locked", 0))),
                    portfolio.get("day_date"),
                    portfolio["day_start_equity"],
                    int(portfolio.get("trades_today", 0)),
                    portfolio.get("last_run_at"),
                    utc_now(),
                    portfolio["strategy_id"],
                ),
            )

    def list_positions(self, strategy_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM dt_positions"
        params: tuple[Any, ...] = ()
        if strategy_id is not None:
            query += " WHERE strategy_id = ?"
            params = (strategy_id,)
        query += " ORDER BY strategy_id, pair"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_position(self, strategy_id: str, pair: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM dt_positions WHERE strategy_id = ? AND pair = ?",
                (strategy_id, pair),
            ).fetchone()
        return dict(row) if row else None

    def save_position(self, position: dict[str, Any]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO dt_positions (
                    strategy_id, pair, side, units, entry_price, stop_price,
                    take_profit, initial_risk, last_price, open_trade_id,
                    opened_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(strategy_id, pair) DO UPDATE SET
                    side = excluded.side,
                    units = excluded.units,
                    entry_price = excluded.entry_price,
                    stop_price = excluded.stop_price,
                    take_profit = excluded.take_profit,
                    initial_risk = excluded.initial_risk,
                    last_price = excluded.last_price,
                    open_trade_id = excluded.open_trade_id,
                    opened_at = excluded.opened_at,
                    updated_at = excluded.updated_at
                """,
                (
                    position["strategy_id"],
                    position["pair"],
                    position["side"],
                    position["units"],
                    position["entry_price"],
                    position["stop_price"],
                    position["take_profit"],
                    position["initial_risk"],
                    position["last_price"],
                    position["open_trade_id"],
                    position["opened_at"],
                    utc_now(),
                ),
            )

    def delete_position(self, strategy_id: str, pair: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM dt_positions WHERE strategy_id = ? AND pair = ?",
                (strategy_id, pair),
            )

    def open_trade(
        self,
        *,
        strategy_id: str,
        pair: str,
        opened_at: str,
        side: str,
        units: float,
        entry_price: float,
        stop_price: float,
        take_profit: float,
        initial_risk: float,
        opened_equity: float,
        entry_fee: float,
    ) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO dt_trades (
                    strategy_id, pair, opened_at, side, units, entry_price,
                    stop_price, take_profit, initial_risk, opened_equity, entry_fee
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    strategy_id,
                    pair,
                    opened_at,
                    side,
                    units,
                    entry_price,
                    stop_price,
                    take_profit,
                    initial_risk,
                    opened_equity,
                    entry_fee,
                ),
            )
            return int(cursor.lastrowid)

    def get_trade(self, trade_id: int) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM dt_trades WHERE id = ?", (trade_id,)
            ).fetchone()
        if row is None:
            raise KeyError(trade_id)
        return dict(row)

    def close_trade(
        self,
        *,
        trade_id: int,
        closed_at: str,
        exit_price: float,
        exit_fee: float,
        pnl: float,
        pnl_pct: float,
        reason: str,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE dt_trades SET
                    closed_at = ?, exit_price = ?, exit_fee = ?, pnl = ?,
                    pnl_pct = ?, reason = ?, status = 'closed'
                WHERE id = ?
                """,
                (closed_at, exit_price, exit_fee, pnl, pnl_pct, reason, trade_id),
            )

    def add_snapshot(
        self,
        *,
        strategy_id: str,
        captured_at: str,
        equity: float,
        realized_balance: float,
        exposure: float,
        drawdown_value: float,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO dt_snapshots (
                    strategy_id, captured_at, equity, realized_balance, exposure, drawdown
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(strategy_id, captured_at) DO UPDATE SET
                    equity = excluded.equity,
                    realized_balance = excluded.realized_balance,
                    exposure = excluded.exposure,
                    drawdown = excluded.drawdown
                """,
                (
                    strategy_id,
                    captured_at,
                    equity,
                    realized_balance,
                    exposure,
                    drawdown_value,
                ),
            )

    def snapshot_series(self, limit: int = 600) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        with self._connect() as connection:
            for strategy in STRATEGIES:
                rows = connection.execute(
                    """
                    SELECT captured_at, equity, drawdown FROM (
                        SELECT captured_at, equity, drawdown
                        FROM dt_snapshots WHERE strategy_id = ?
                        ORDER BY captured_at DESC LIMIT ?
                    ) ORDER BY captured_at ASC
                    """,
                    (strategy.strategy_id, limit),
                ).fetchall()
                result[strategy.strategy_id] = [dict(row) for row in rows]
        return result

    def recent_trades(self, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM dt_trades ORDER BY id DESC LIMIT ?", (safe_limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def save_market(self, snapshot: SignalSnapshot, source: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO dt_markets (
                    pair, candle_time, price, signal, trend, rsi, reason, source, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pair) DO UPDATE SET
                    candle_time = excluded.candle_time,
                    price = excluded.price,
                    signal = excluded.signal,
                    trend = excluded.trend,
                    rsi = excluded.rsi,
                    reason = excluded.reason,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                (
                    snapshot.pair,
                    snapshot.candle_time,
                    snapshot.price,
                    snapshot.direction,
                    snapshot.trend,
                    snapshot.rsi,
                    snapshot.reason,
                    source,
                    utc_now(),
                ),
            )

    def get_market(self, pair: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM dt_markets WHERE pair = ?", (pair,)
            ).fetchone()
        return dict(row) if row else None

    def list_markets(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM dt_markets ORDER BY pair").fetchall()
        return [dict(row) for row in rows]

    def set_cooldown(self, strategy_id: str, pair: str, until_at: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO dt_cooldowns(strategy_id, pair, until_at) VALUES (?, ?, ?)
                ON CONFLICT(strategy_id, pair) DO UPDATE SET until_at = excluded.until_at
                """,
                (strategy_id, pair, until_at),
            )

    def get_cooldown(self, strategy_id: str, pair: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT until_at FROM dt_cooldowns WHERE strategy_id = ? AND pair = ?",
                (strategy_id, pair),
            ).fetchone()
        return str(row["until_at"]) if row else None

    def add_event(self, level: str, strategy_id: str | None, message: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO dt_events(created_at, level, strategy_id, message) VALUES (?, ?, ?, ?)",
                (utc_now(), level, strategy_id, message),
            )

    def recent_events(self, limit: int = 30) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM dt_events ORDER BY id DESC LIMIT ?", (safe_limit,)
            ).fetchall()
        return [dict(row) for row in rows]
