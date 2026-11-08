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
    """SQLite persistence for the spot trend-following paper simulator.

    The ``tf_`` prefix (v0.3) keeps the data of older versions (``dt_``
    intraday tables) untouched in the same file instead of migrating it.
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

    def _query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]
        finally:
            connection.close()

    def _write(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self._lock:
            connection = self._connect()
            try:
                with connection:
                    cursor = connection.execute(sql, params)
                return int(cursor.lastrowid or 0)
            finally:
                connection.close()

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS tf_portfolios (
            strategy_id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            starting_capital REAL NOT NULL,
            realized_balance REAL NOT NULL,
            peak_equity REAL NOT NULL,
            fees_paid REAL NOT NULL DEFAULT 0,
            last_run_at TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tf_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            pair TEXT NOT NULL,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            units REAL NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            entry_fee REAL NOT NULL DEFAULT 0,
            exit_fee REAL NOT NULL DEFAULT 0,
            entry_fill_source TEXT NOT NULL DEFAULT 'candle',
            exit_fill_source TEXT,
            pnl REAL,
            pnl_pct REAL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            FOREIGN KEY (strategy_id) REFERENCES tf_portfolios(strategy_id)
        );

        CREATE TABLE IF NOT EXISTS tf_positions (
            strategy_id TEXT NOT NULL,
            pair TEXT NOT NULL,
            units REAL NOT NULL,
            entry_price REAL NOT NULL,
            exit_level REAL NOT NULL,
            last_price REAL NOT NULL,
            open_trade_id INTEGER NOT NULL,
            opened_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(strategy_id, pair),
            FOREIGN KEY (strategy_id) REFERENCES tf_portfolios(strategy_id),
            FOREIGN KEY (open_trade_id) REFERENCES tf_trades(id)
        );

        CREATE TABLE IF NOT EXISTS tf_snapshots (
            strategy_id TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            equity REAL NOT NULL,
            cash REAL NOT NULL,
            exposure REAL NOT NULL,
            drawdown REAL NOT NULL,
            PRIMARY KEY(strategy_id, captured_at),
            FOREIGN KEY (strategy_id) REFERENCES tf_portfolios(strategy_id)
        );

        CREATE TABLE IF NOT EXISTS tf_markets (
            pair TEXT PRIMARY KEY,
            candle_time TEXT NOT NULL,
            price REAL NOT NULL,
            signal INTEGER NOT NULL,
            entry_level REAL NOT NULL,
            exit_level REAL NOT NULL,
            reason TEXT NOT NULL,
            source TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tf_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            level TEXT NOT NULL,
            strategy_id TEXT,
            message TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_tf_trades_strategy ON tf_trades(strategy_id, id DESC);
        """
        with self._lock:
            connection = self._connect()
            try:
                connection.executescript(schema)
                now = utc_now()
                with connection:
                    for strategy in STRATEGIES:
                        connection.execute(
                            """
                            INSERT OR IGNORE INTO tf_portfolios (
                                strategy_id, label, starting_capital, realized_balance,
                                peak_equity, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                strategy.strategy_id,
                                strategy.label,
                                self.starting_capital,
                                self.starting_capital,
                                self.starting_capital,
                                now,
                            ),
                        )
            finally:
                connection.close()

    def reset(self) -> None:
        tables = ("tf_positions", "tf_snapshots", "tf_trades", "tf_markets", "tf_events", "tf_portfolios")
        with self._lock:
            connection = self._connect()
            try:
                with connection:
                    for table in tables:
                        connection.execute(f"DELETE FROM {table}")
            finally:
                connection.close()
        self.initialize()
        self.add_event("warning", None, "I reset the paper account.")

    # -- portfolios ---------------------------------------------------------

    def get_portfolio(self, strategy_id: str) -> dict[str, Any]:
        rows = self._query("SELECT * FROM tf_portfolios WHERE strategy_id = ?", (strategy_id,))
        if not rows:
            raise KeyError(strategy_id)
        return rows[0]

    def list_portfolios(self) -> list[dict[str, Any]]:
        known = {strategy.strategy_id for strategy in STRATEGIES}
        return [row for row in self._query("SELECT * FROM tf_portfolios") if row["strategy_id"] in known]

    def save_portfolio(self, portfolio: dict[str, Any]) -> None:
        self._write(
            """
            UPDATE tf_portfolios SET realized_balance = ?, peak_equity = ?, fees_paid = ?,
                last_run_at = ?, updated_at = ?
            WHERE strategy_id = ?
            """,
            (
                portfolio["realized_balance"],
                portfolio["peak_equity"],
                portfolio["fees_paid"],
                portfolio.get("last_run_at"),
                utc_now(),
                portfolio["strategy_id"],
            ),
        )

    # -- positions ----------------------------------------------------------

    def list_positions(self, strategy_id: str | None = None) -> list[dict[str, Any]]:
        if strategy_id is None:
            return self._query("SELECT * FROM tf_positions ORDER BY strategy_id, pair")
        return self._query(
            "SELECT * FROM tf_positions WHERE strategy_id = ? ORDER BY pair", (strategy_id,)
        )

    def save_position(self, position: dict[str, Any]) -> None:
        self._write(
            """
            INSERT INTO tf_positions (
                strategy_id, pair, units, entry_price, exit_level, last_price,
                open_trade_id, opened_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(strategy_id, pair) DO UPDATE SET
                units = excluded.units,
                entry_price = excluded.entry_price,
                exit_level = excluded.exit_level,
                last_price = excluded.last_price,
                open_trade_id = excluded.open_trade_id,
                opened_at = excluded.opened_at,
                updated_at = excluded.updated_at
            """,
            (
                position["strategy_id"],
                position["pair"],
                position["units"],
                position["entry_price"],
                position["exit_level"],
                position["last_price"],
                position["open_trade_id"],
                position["opened_at"],
                utc_now(),
            ),
        )

    def delete_position(self, strategy_id: str, pair: str) -> None:
        self._write(
            "DELETE FROM tf_positions WHERE strategy_id = ? AND pair = ?", (strategy_id, pair)
        )

    # -- trades -------------------------------------------------------------

    def open_trade(
        self,
        *,
        strategy_id: str,
        pair: str,
        opened_at: str,
        units: float,
        entry_price: float,
        entry_fee: float,
        fill_source: str,
    ) -> int:
        return self._write(
            """
            INSERT INTO tf_trades (
                strategy_id, pair, opened_at, units, entry_price, entry_fee, entry_fill_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (strategy_id, pair, opened_at, units, entry_price, entry_fee, fill_source),
        )

    def get_trade(self, trade_id: int) -> dict[str, Any]:
        rows = self._query("SELECT * FROM tf_trades WHERE id = ?", (trade_id,))
        if not rows:
            raise KeyError(trade_id)
        return rows[0]

    def close_trade(
        self,
        *,
        trade_id: int,
        closed_at: str,
        exit_price: float,
        exit_fee: float,
        fill_source: str,
        pnl: float,
        pnl_pct: float,
        reason: str,
    ) -> None:
        self._write(
            """
            UPDATE tf_trades SET closed_at = ?, exit_price = ?, exit_fee = ?, exit_fill_source = ?,
                pnl = ?, pnl_pct = ?, reason = ?, status = 'closed'
            WHERE id = ?
            """,
            (closed_at, exit_price, exit_fee, fill_source, pnl, pnl_pct, reason, trade_id),
        )

    def recent_trades(self, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        return self._query("SELECT * FROM tf_trades ORDER BY id DESC LIMIT ?", (safe_limit,))

    def trade_stats(self, strategy_id: str) -> dict[str, Any]:
        rows = self._query(
            """
            SELECT COUNT(*) AS closed, SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS wins
            FROM tf_trades WHERE strategy_id = ? AND status = 'closed'
            """,
            (strategy_id,),
        )
        closed = int(rows[0]["closed"] or 0)
        wins = int(rows[0]["wins"] or 0)
        return {"closed_trades": closed, "win_rate_pct": round(wins / closed * 100, 1) if closed else None}

    # -- snapshots ----------------------------------------------------------

    def add_snapshot(
        self,
        *,
        strategy_id: str,
        captured_at: str,
        equity: float,
        cash: float,
        exposure: float,
        drawdown_value: float,
    ) -> None:
        self._write(
            """
            INSERT INTO tf_snapshots (strategy_id, captured_at, equity, cash, exposure, drawdown)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(strategy_id, captured_at) DO UPDATE SET
                equity = excluded.equity, cash = excluded.cash,
                exposure = excluded.exposure, drawdown = excluded.drawdown
            """,
            (strategy_id, captured_at, equity, cash, exposure, drawdown_value),
        )

    def snapshot_series(self, limit: int = 1_500) -> dict[str, list[dict[str, Any]]]:
        return {
            strategy.strategy_id: self._query(
                """
                SELECT captured_at, equity, drawdown FROM (
                    SELECT captured_at, equity, drawdown FROM tf_snapshots
                    WHERE strategy_id = ? ORDER BY captured_at DESC LIMIT ?
                ) ORDER BY captured_at ASC
                """,
                (strategy.strategy_id, limit),
            )
            for strategy in STRATEGIES
        }

    # -- markets ------------------------------------------------------------

    def save_market(self, snapshot: SignalSnapshot, source: str) -> None:
        self._write(
            """
            INSERT INTO tf_markets (
                pair, candle_time, price, signal, entry_level, exit_level, reason, source, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pair) DO UPDATE SET
                candle_time = excluded.candle_time, price = excluded.price,
                signal = excluded.signal, entry_level = excluded.entry_level,
                exit_level = excluded.exit_level, reason = excluded.reason,
                source = excluded.source, updated_at = excluded.updated_at
            """,
            (
                snapshot.pair,
                snapshot.candle_time,
                snapshot.price,
                snapshot.direction,
                snapshot.entry_level,
                snapshot.exit_level,
                snapshot.reason,
                source,
                utc_now(),
            ),
        )

    def get_market(self, pair: str) -> dict[str, Any] | None:
        rows = self._query("SELECT * FROM tf_markets WHERE pair = ?", (pair,))
        return rows[0] if rows else None

    def list_markets(self) -> list[dict[str, Any]]:
        return self._query("SELECT * FROM tf_markets ORDER BY pair")

    # -- events -------------------------------------------------------------

    def add_event(self, level: str, strategy_id: str | None, message: str) -> None:
        self._write(
            "INSERT INTO tf_events(created_at, level, strategy_id, message) VALUES (?, ?, ?, ?)",
            (utc_now(), level, strategy_id, message),
        )

    def recent_events(self, limit: int = 30) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        return self._query("SELECT * FROM tf_events ORDER BY id DESC LIMIT ?", (safe_limit,))
