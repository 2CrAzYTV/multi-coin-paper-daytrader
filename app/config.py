from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from os import getenv
from pathlib import Path


PAIR_PATTERN = re.compile(r"^[A-Z0-9]{2,12}-EUR$")
ALLOWED_INTERVALS = {"4h", "1d"}
DEFAULT_PAIRS = ("BTC-EUR", "ETH-EUR", "SOL-EUR", "XRP-EUR")
# Bitpanda Fusion charges 0.25% per order (maker and taker) in the entry
# volume tier (< EUR 100,000 traded in 30 days).
FUSION_ENTRY_TIER_FEE = 0.0025


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
    if not value or not value.strip():
        return DEFAULT_PAIRS
    return tuple(
        dict.fromkeys(item.strip().upper() for item in value.split(",") if item.strip())
    )


@dataclass(frozen=True)
class Settings:
    """Spot trend-following paper simulator (long only, no leverage)."""

    app_name: str = "Multi-Coin Paper Trader"
    app_language: str = "en"
    paper_only: bool = True
    starting_capital: float = 1_000.0
    fee_rate: float = FUSION_ENTRY_TIER_FEE
    slippage_rate: float = 0.0005
    use_order_book: bool = True
    entry_window: int = 55
    exit_window: int = 20
    atr_window: int = 20
    max_open_positions: int = 4
    pairs: tuple[str, ...] = DEFAULT_PAIRS
    candle_interval: str = "1d"
    history_bars: int = 120
    backtest_bars: int = 1_440
    data_source: str = "demo"
    data_dir: Path = Path("data")
    timezone: str = "Europe/Berlin"
    poll_seconds: int = 300
    fusion_read_api_key: str = ""
    fusion_base_url: str = "https://api.fusion.bitpanda.com"

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            app_language=getenv("APP_LANGUAGE", "en").strip().lower(),
            paper_only=_as_bool(getenv("PAPER_ONLY"), True),
            starting_capital=_as_float("STARTING_CAPITAL", 1_000.0),
            fee_rate=_as_float("FEE_RATE", FUSION_ENTRY_TIER_FEE),
            slippage_rate=_as_float("SLIPPAGE_RATE", 0.0005),
            use_order_book=_as_bool(getenv("USE_ORDER_BOOK"), True),
            entry_window=_as_int("ENTRY_WINDOW", 55),
            exit_window=_as_int("EXIT_WINDOW", 20),
            atr_window=_as_int("ATR_WINDOW", 20),
            max_open_positions=_as_int("MAX_OPEN_POSITIONS", 4),
            pairs=_as_pairs(getenv("PAIRS")),
            candle_interval=getenv("CANDLE_INTERVAL", "1d").strip(),
            history_bars=_as_int("HISTORY_BARS", 120),
            backtest_bars=_as_int("BACKTEST_BARS", 1_440),
            data_source=getenv("DATA_SOURCE", "demo").strip().lower(),
            data_dir=Path(getenv("DATA_DIR", "data")),
            timezone=getenv("APP_TIMEZONE", "Europe/Berlin").strip(),
            poll_seconds=_as_int("POLL_SECONDS", 300),
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
        if not 0 <= self.fee_rate <= 0.01:
            raise ValueError("I require FEE_RATE to be between 0 and 0.01.")
        if not 0 <= self.slippage_rate <= 0.01:
            raise ValueError("I require SLIPPAGE_RATE to be between 0 and 0.01.")
        if not 2 <= self.exit_window < self.entry_window <= 250:
            raise ValueError(
                "I require 2 <= EXIT_WINDOW < ENTRY_WINDOW <= 250."
            )
        if not 2 <= self.atr_window <= 100:
            raise ValueError("I require ATR_WINDOW to be between 2 and 100.")
        if self.candle_interval not in ALLOWED_INTERVALS:
            raise ValueError("I require CANDLE_INTERVAL to be 4h or 1d.")
        if self.data_source not in {"fusion", "demo"}:
            raise ValueError("I require DATA_SOURCE to be either fusion or demo.")
        if self.data_source == "fusion" and not self.fusion_read_api_key:
            raise ValueError(
                "I require FUSION_READ_API_KEY for Fusion data and accept a "
                "Bitpanda key with Read permission only."
            )
        minimum_history = self.entry_window + 2
        if not minimum_history <= self.history_bars <= 1_440:
            raise ValueError(
                f"I require HISTORY_BARS between {minimum_history} and 1440."
            )
        if not 100 <= self.backtest_bars <= 1_440:
            raise ValueError("I require BACKTEST_BARS between 100 and 1440.")
        if not 30 <= self.poll_seconds <= 3_600:
            raise ValueError("I require POLL_SECONDS to be between 30 and 3600.")
        if (
            not 1 <= len(self.pairs) <= 10
            or any(not PAIR_PATTERN.match(pair) for pair in self.pairs)
        ):
            raise ValueError("I require PAIRS to contain 1 to 10 unique EUR pairs.")
        if not 1 <= self.max_open_positions <= len(self.pairs):
            raise ValueError(
                "I require MAX_OPEN_POSITIONS between 1 and the number of PAIRS."
            )

    @property
    def database_path(self) -> Path:
        return self.data_dir / "paper_trading.sqlite3"

    def public_dict(self) -> dict:
        values = asdict(self)
        values.pop("fusion_read_api_key", None)
        values["data_dir"] = str(self.data_dir)
        values["pairs"] = list(self.pairs)
        values["fusion_key_configured"] = bool(self.fusion_read_api_key)
        values["position_share"] = round(1 / len(self.pairs), 4)
        values["round_trip_cost"] = round(2 * (self.fee_rate + self.slippage_rate), 5)
        return values
