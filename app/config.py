from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from os import getenv
from pathlib import Path


PAIR_PATTERN = re.compile(r"^[A-Z0-9]{2,12}-EUR$")
ALLOWED_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "ja"}


def _as_float(name: str, default: float) -> float:
    raw = getenv(name)
    return default if raw is None or not raw.strip() else float(raw)


def _as_int(name: str, default: int) -> int:
    raw = getenv(name)
    return default if raw is None or not raw.strip() else int(raw)


def _as_pairs(value: str | None) -> tuple[str, ...]:
    raw = value or "BTC-EUR,ETH-EUR,SOL-EUR,XRP-EUR,ADA-EUR"
    return tuple(
        dict.fromkeys(item.strip().upper() for item in raw.split(",") if item.strip())
    )


@dataclass(frozen=True)
class Settings:
    app_name: str = "Multi-Coin Paper Daytrader"
    paper_only: bool = True
    starting_capital: float = 1_000.0
    risk_per_trade: float = 0.005
    max_aggregate_risk: float = 0.01
    max_daily_loss: float = 0.02
    hard_drawdown: float = 0.10
    max_open_positions: int = 2
    max_trades_per_day: int = 3
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005
    fast_window: int = 9
    slow_window: int = 21
    trend_fast_window: int = 20
    trend_slow_window: int = 50
    atr_window: int = 14
    rsi_window: int = 14
    stop_atr_multiple: float = 1.5
    minimum_stop_pct: float = 0.006
    take_profit_r: float = 2.0
    trailing_trigger_r: float = 1.0
    pairs: tuple[str, ...] = (
        "BTC-EUR",
        "ETH-EUR",
        "SOL-EUR",
        "XRP-EUR",
        "ADA-EUR",
    )
    candle_interval: str = "15m"
    trend_interval: str = "1h"
    history_bars: int = 500
    backtest_bars: int = 1_000
    data_source: str = "demo"
    data_dir: Path = Path("data")
    timezone: str = "Europe/Berlin"
    poll_seconds: int = 60
    session_close_hour: int = 23
    session_close_minute: int = 45
    cooldown_minutes: int = 45
    fusion_read_api_key: str = ""
    fusion_base_url: str = "https://api.fusion.bitpanda.com"

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            paper_only=_as_bool(getenv("PAPER_ONLY"), True),
            starting_capital=_as_float("STARTING_CAPITAL", 1_000.0),
            risk_per_trade=_as_float("RISK_PER_TRADE", 0.005),
            max_aggregate_risk=_as_float("MAX_AGGREGATE_RISK", 0.01),
            max_daily_loss=_as_float("MAX_DAILY_LOSS", 0.02),
            hard_drawdown=_as_float("HARD_DRAWDOWN", 0.10),
            max_open_positions=_as_int("MAX_OPEN_POSITIONS", 2),
            max_trades_per_day=_as_int("MAX_TRADES_PER_DAY", 3),
            fee_rate=_as_float("FEE_RATE", 0.001),
            slippage_rate=_as_float("SLIPPAGE_RATE", 0.0005),
            fast_window=_as_int("FAST_WINDOW", 9),
            slow_window=_as_int("SLOW_WINDOW", 21),
            trend_fast_window=_as_int("TREND_FAST_WINDOW", 20),
            trend_slow_window=_as_int("TREND_SLOW_WINDOW", 50),
            atr_window=_as_int("ATR_WINDOW", 14),
            rsi_window=_as_int("RSI_WINDOW", 14),
            stop_atr_multiple=_as_float("STOP_ATR_MULTIPLE", 1.5),
            minimum_stop_pct=_as_float("MINIMUM_STOP_PCT", 0.006),
            take_profit_r=_as_float("TAKE_PROFIT_R", 2.0),
            trailing_trigger_r=_as_float("TRAILING_TRIGGER_R", 1.0),
            pairs=_as_pairs(getenv("PAIRS")),
            candle_interval=getenv("CANDLE_INTERVAL", "15m").strip(),
            trend_interval=getenv("TREND_INTERVAL", "1h").strip(),
            history_bars=_as_int("HISTORY_BARS", 500),
            backtest_bars=_as_int("BACKTEST_BARS", 1_000),
            data_source=getenv("DATA_SOURCE", "demo").strip().lower(),
            data_dir=Path(getenv("DATA_DIR", "data")),
            timezone=getenv("APP_TIMEZONE", "Europe/Berlin").strip(),
            poll_seconds=_as_int("POLL_SECONDS", 60),
            session_close_hour=_as_int("SESSION_CLOSE_HOUR", 23),
            session_close_minute=_as_int("SESSION_CLOSE_MINUTE", 45),
            cooldown_minutes=_as_int("COOLDOWN_MINUTES", 45),
            fusion_read_api_key=getenv("FUSION_READ_API_KEY", "").strip(),
            fusion_base_url=getenv(
                "FUSION_BASE_URL", "https://api.fusion.bitpanda.com"
            ).rstrip("/"),
        )
        settings.validate()
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        return settings

    def validate(self) -> None:
        if not self.paper_only:
            raise ValueError(
                "PAPER_ONLY muss true bleiben. Diese Version kann keine Echtgeldorders ausfuehren."
            )
        if self.starting_capital <= 0:
            raise ValueError("STARTING_CAPITAL muss groesser als 0 sein.")
        if not 0 < self.risk_per_trade <= 0.01:
            raise ValueError("RISK_PER_TRADE muss zwischen 0 und 0.01 liegen.")
        if not self.risk_per_trade <= self.max_aggregate_risk <= 0.02:
            raise ValueError("MAX_AGGREGATE_RISK muss zwischen Trade-Risiko und 0.02 liegen.")
        if not self.max_aggregate_risk <= self.max_daily_loss <= 0.02:
            raise ValueError("MAX_DAILY_LOSS muss zwischen Gesamtrisiko und 0.02 liegen.")
        if not 0.02 <= self.hard_drawdown <= 0.25:
            raise ValueError("HARD_DRAWDOWN muss zwischen 0.02 und 0.25 liegen.")
        if not 1 <= self.max_open_positions <= 3:
            raise ValueError("MAX_OPEN_POSITIONS muss zwischen 1 und 3 liegen.")
        if not 1 <= self.max_trades_per_day <= 6:
            raise ValueError("MAX_TRADES_PER_DAY muss zwischen 1 und 6 liegen.")
        if not 2 <= self.fast_window < self.slow_window:
            raise ValueError("FAST_WINDOW muss kleiner als SLOW_WINDOW sein.")
        if not 2 <= self.trend_fast_window < self.trend_slow_window:
            raise ValueError("TREND_FAST_WINDOW muss kleiner als TREND_SLOW_WINDOW sein.")
        if (
            self.candle_interval not in ALLOWED_INTERVALS
            or self.trend_interval not in ALLOWED_INTERVALS
        ):
            raise ValueError("Nicht unterstuetztes Kerzenintervall.")
        if self.data_source not in {"fusion", "demo"}:
            raise ValueError("DATA_SOURCE muss fusion oder demo sein.")
        if self.data_source == "fusion" and not self.fusion_read_api_key:
            raise ValueError(
                "FUSION_READ_API_KEY fehlt. Nur einen Bitpanda-Fusion-Schluessel mit Read-Recht verwenden."
            )
        if not 60 <= self.history_bars <= 1_000 or not 100 <= self.backtest_bars <= 5_000:
            raise ValueError("HISTORY_BARS oder BACKTEST_BARS ausserhalb der Sicherheitsgrenzen.")
        if not 30 <= self.poll_seconds <= 900:
            raise ValueError("POLL_SECONDS muss zwischen 30 und 900 liegen.")
        if (
            not 0 <= self.session_close_hour <= 23
            or not 0 <= self.session_close_minute <= 59
        ):
            raise ValueError("Ungueltiger taeglicher Sitzungsabschluss.")
        if (
            not 1 <= len(self.pairs) <= 10
            or any(not PAIR_PATTERN.match(pair) for pair in self.pairs)
        ):
            raise ValueError("PAIRS muss 1 bis 10 eindeutige EUR-Paare enthalten.")

    @property
    def database_path(self) -> Path:
        return self.data_dir / "paper_trading.sqlite3"

    def public_dict(self) -> dict:
        values = asdict(self)
        values.pop("fusion_read_api_key", None)
        values["data_dir"] = str(self.data_dir)
        values["pairs"] = list(self.pairs)
        values["fusion_key_configured"] = bool(self.fusion_read_api_key)
        values["risk_amount"] = round(self.starting_capital * self.risk_per_trade, 2)
        values["aggregate_risk_amount"] = round(
            self.starting_capital * self.max_aggregate_risk, 2
        )
        values["daily_loss_amount"] = round(
            self.starting_capital * self.max_daily_loss, 2
        )
        return values
