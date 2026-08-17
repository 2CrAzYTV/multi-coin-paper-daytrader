from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from .config import Settings
from .models import PairConstraint

INTERVAL_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1_800, "1h": 3_600, "4h": 14_400, "1d": 86_400}
PANDAS_FREQUENCIES = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D"}
DEMO_START_PRICES = {"BTC-EUR": 92_000.0, "ETH-EUR": 3_400.0, "SOL-EUR": 165.0, "XRP-EUR": 2.15, "ADA-EUR": 0.72, "LINK-EUR": 19.0, "AVAX-EUR": 28.0, "SUI-EUR": 3.2, "TAO-EUR": 340.0, "DOGE-EUR": 0.21}

class MarketDataError(RuntimeError): pass

class MarketData:
    """GET-only Bitpanda Fusion market-data reader plus deterministic demo data."""
    def __init__(self, settings: Settings): self.settings = settings

    def history(self, pair: str, interval: str | None = None, limit: int | None = None) -> pd.DataFrame:
        selected_interval = interval or self.settings.candle_interval
        selected_limit = min(5_000, limit or self.settings.history_bars)
        if self.settings.data_source == "demo": return self._demo_history(pair, selected_interval, selected_limit)
        return self._fusion_history(pair, selected_interval, selected_limit)

    def pair_constraints(self) -> dict[str, PairConstraint]:
        if self.settings.data_source == "demo": return {pair: PairConstraint(pair=pair) for pair in self.settings.pairs}
        payload = self._get_json("/v1/pairs")
        if not isinstance(payload, list): raise MarketDataError("I did not receive a valid pair list from Bitpanda Fusion.")
        requested = set(self.settings.pairs); constraints = {}
        for item in payload:
            pair = str(item.get("pair", "")).upper()
            if pair not in requested: continue
            try:
                constraints[pair] = PairConstraint(pair=pair, min_order_amount=float(item.get("minOrderAmount") or 25.0), max_order_amount=float(item.get("maxOrderAmount") or 1_000_000.0), size_increment=float(item.get("sizeIncrement") or 0.00000001))
            except (TypeError, ValueError) as exc: raise MarketDataError(f"I received invalid trading constraints for {pair}.") from exc
        if not constraints: raise MarketDataError("I found none of the configured EUR pairs active on Bitpanda Fusion.")
        return constraints

    def available_eur_pairs(self) -> tuple[str, ...]:
        """Discover active EUR instruments from Fusion without enabling trading methods."""
        if self.settings.data_source == "demo": return tuple(self.settings.pairs)
        payload = self._get_json("/v1/pairs")
        if not isinstance(payload, list): raise MarketDataError("I did not receive a valid pair list from Bitpanda Fusion.")
        return tuple(sorted({str(item.get("pair", "")).upper() for item in payload if str(item.get("pair", "")).upper().endswith("-EUR")}))

    def _fusion_history(self, pair: str, interval: str, limit: int) -> pd.DataFrame:
        # Fusion may cap one candle response. Fetch backwards in chunks and de-duplicate.
        remaining = min(5_000, limit); chunks: list[pd.DataFrame] = []; before: int | None = None
        while remaining > 0:
            request_limit = min(1_000, remaining); params: dict[str, Any] = {"interval": interval, "limit": request_limit}
            if before is not None: params["to"] = before
            payload = self._get_json(f"/v1/candles/{pair}", params=params)
            if not isinstance(payload, list) or not payload: break
            try:
                data = pd.DataFrame(payload).rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"})
                data.index = pd.to_datetime(data.pop("timestamp"), unit="s", utc=True)
            except Exception as exc: raise MarketDataError(f"I could not parse Fusion candles for {pair}.") from exc
            data = self._normalize(data, pair); chunks.append(data); remaining -= len(data)
            oldest = int(data.index.min().timestamp()); next_before = oldest - INTERVAL_SECONDS[interval]
            if before is not None and next_before >= before: break
            before = next_before
            if len(data) < request_limit: break
        if not chunks: raise MarketDataError(f"I received no Fusion candles for {pair}.")
        data = pd.concat(chunks); data = data[~data.index.duplicated(keep="last")].sort_index().tail(limit)
        seconds = INTERVAL_SECONDS[interval]; now = datetime.now(UTC).timestamp()
        if len(data) > 1 and data.index[-1].timestamp() + seconds > now - 5: data = data.iloc[:-1]
        return data

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not self.settings.fusion_read_api_key: raise MarketDataError("I require a Fusion API key with Read permission when DATA_SOURCE=fusion.")
        try:
            import httpx
            with httpx.Client(base_url=self.settings.fusion_base_url, headers={"x-api-key": self.settings.fusion_read_api_key, "Accept":"application/json"}, timeout=20) as client:
                response=client.get(path, params=params); response.raise_for_status(); return response.json()
        except Exception as exc:
            status=getattr(getattr(exc,"response",None),"status_code",None); detail=f"HTTP {status}" if status else type(exc).__name__
            raise MarketDataError(f"I could not retrieve Bitpanda Fusion data ({detail}).") from exc

    @staticmethod
    def _normalize(data: pd.DataFrame, pair: str) -> pd.DataFrame:
        required=["Open","High","Low","Close","Volume"]; missing=[c for c in required if c not in data.columns]
        if missing: raise MarketDataError(f"I received market data for {pair} without these columns: {missing}")
        clean=data[required].copy()
        for column in required: clean[column]=pd.to_numeric(clean[column], errors="coerce")
        clean=clean.dropna(); clean.index=pd.to_datetime(clean.index, utc=True); clean=clean[~clean.index.duplicated(keep="last")].sort_index()
        if len(clean)<60: raise MarketDataError(f"I received too few candles for {pair}: {len(clean)} instead of at least 60.")
        return clean.astype(float)

    @staticmethod
    def _demo_history(pair: str, interval: str, limit: int) -> pd.DataFrame:
        seconds=INTERVAL_SECONDS[interval]; now_seconds=int(datetime.now(UTC).timestamp()); closed_open=((now_seconds//seconds)-1)*seconds
        end=pd.Timestamp(closed_open, unit="s", tz="UTC"); index=pd.date_range(end=end, periods=limit, freq=PANDAS_FREQUENCIES[interval])
        seed=int(hashlib.sha256(f"{pair}:{interval}:paper-daytrader".encode()).hexdigest()[:8],16); rng=np.random.default_rng(seed); scale=(seconds/900)**0.5
        base=DEMO_START_PRICES.get(pair,100.0); wave=np.sin(np.linspace(0,16*np.pi,limit))*0.0014*scale; returns=rng.normal(0.00002*scale,0.0038*scale,limit)+wave
        close=base*np.exp(np.cumsum(returns)); open_price=np.r_[close[0],close[:-1]]*(1+rng.normal(0,0.00035*scale,limit)); wick=np.abs(rng.normal(0.0018*scale,0.0008*scale,limit))
        high=np.maximum(open_price,close)*(1+wick); low=np.minimum(open_price,close)*(1-wick); volume=rng.lognormal(mean=8.5,sigma=0.55,size=limit)*(base/close)
        return pd.DataFrame({"Open":open_price,"High":high,"Low":low,"Close":close,"Volume":volume}, index=index)
