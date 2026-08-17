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
    app_language: str = "en"
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
    signal_min_strength: float = 0.12
    trend_min_strength_pct: float = 0.001
    volume_multiplier: float = 1.0
    long_rsi_min: float = 48.0
    long_rsi_max: float = 64.0
    short_rsi_min: float = 36.0
    short_rsi_max: float = 52.0
    exit_confirmation_bars: int = 2
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
            app_language=getenv("APP_LANGUAGE", "en").strip().lower(),
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
            signal_min_strength=_as_float("SIGNAL_MIN_STRENGTH", 0.12),
            trend_min_strength_pct=_as_float("TREND_MIN_STRENGTH_PCT", 0.001),
            volume_multiplier=_as_float("VOLUME_MULTIPLIER", 1.0),
            long_rsi_min=_as_float("LONG_RSI_MIN", 48.0),
            long_rsi_max=_as_float("LONG_RSI_MAX", 64.0),
            short_rsi_min=_as_float("SHORT_RSI_MIN", 36.0),
            short_rsi_max=_as_float("SHORT_RSI_MAX", 52.0),
            exit_confirmation_bars=_as_int("EXIT_CONFIRMATION_BARS", 2),
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
        if self.app_language not in {"en", "de"}:
            raise ValueError("I require APP_LANGUAGE to be either en or de.")
        if not self.paper_only:
            raise ValueError(
                "I require PAPER_ONLY=true. This version cannot place real-money orders."
            )
        if self.starting_capital <= 0:
            raise ValueError("I require STARTING_CAPITAL to be greater than 0.")
        if not 0 < self.risk_per_trade <= 0.01:
            raise ValueError("I require RISK_PER_TRADE to be greater than 0 and no more than 0.01.")
        if not self.risk_per_trade <= self.max_aggregate_risk <= 0.02:
            raise ValueError(
                "I require MAX_AGGREGATE_RISK to be between the per-trade risk and 0.02."
            )
        if not self.max_aggregate_risk <= self.max_daily_loss <= 0.02:
            raise ValueError("I require MAX_DAILY_LOSS to be between aggregate risk and 0.02.")
        if not 0.02 <= self.hard_drawdown <= 0.25:
            raise ValueError("I require HARD_DRAWDOWN to be between 0.02 and 0.25.")
        if not 1 <= self.max_open_positions <= 3:
            raise ValueError("I require MAX_OPEN_POSITIONS to be between 1 and 3.")
        if not 1 <= self.max_trades_per_day <= 6:
            raise ValueError("I require MAX_TRADES_PER_DAY to be between 1 and 6.")
        if not 2 <= self.fast_window < self.slow_window:
            raise ValueError("I require FAST_WINDOW to be smaller than SLOW_WINDOW.")
        if not 2 <= self.trend_fast_window < self.trend_slow_window:
            raise ValueError("I require TREND_FAST_WINDOW to be smaller than TREND_SLOW_WINDOW.")
        if not 0 <= self.signal_min_strength <= 2:
            raise ValueError("I require SIGNAL_MIN_STRENGTH to be between 0 and 2.")
        if not 0 <= self.trend_min_strength_pct <= 0.05:
            raise ValueError("I require TREND_MIN_STRENGTH_PCT to be between 0 and 0.05.")
        if not 0.5 <= self.volume_multiplier <= 3:
            raise ValueError("I require VOLUME_MULTIPLIER to be between 0.5 and 3.")
        if not 0 <= self.long_rsi_min < self.long_rsi_max <= 100:
            raise ValueError("I received invalid long RSI bounds.")
        if not 0 <= self.short_rsi_min < self.short_rsi_max <= 100:
            raise ValueError("I received invalid short RSI bounds.")
        if not 1 <= self.exit_confirmation_bars <= 4:
            raise ValueError("I require EXIT_CONFIRMATION_BARS to be between 1 and 4.")
        if (
            self.candle_interval not in ALLOWED_INTERVALS
            or self.trend_interval not in ALLOWED_INTERVALS
        ):
            raise ValueError("I received an unsupported candle interval.")
        if self.data_source not in {"fusion", "demo"}:
            raise ValueError("I require DATA_SOURCE to be either fusion or demo.")
        if self.data_source == "fusion" and not self.fusion_read_api_key:
            raise ValueError(
                "I require FUSION_READ_API_KEY for Fusion data and accept a Bitpanda key with Read permission only."
            )
        if not 60 <= self.history_bars <= 1_000 or not 100 <= self.backtest_bars <= 5_000:
            raise ValueError("I received HISTORY_BARS or BACKTEST_BARS outside the safety limits.")
        if not 30 <= self.poll_seconds <= 900:
            raise ValueError("I require POLL_SECONDS to be between 30 and 900.")
        if (
            not 0 <= self.session_close_hour <= 23
            or not 0 <= self.session_close_minute <= 59
        ):
            raise ValueError("I received an invalid daily session close time.")
        if (
            not 1 <= len(self.pairs) <= 10
            or any(not PAIR_PATTERN.match(pair) for pair in self.pairs)
        ):
            raise ValueError("I require PAIRS to contain 1 to 10 unique EUR pairs.")

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
