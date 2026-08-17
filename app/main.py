from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .backtest import Backtester
from .config import Settings
from .db import Repository
from .engine import PaperEngine
from .market_data import MarketData, MarketDataError
from .scheduler import scheduler_loop


settings = Settings.from_env()
repository = Repository(settings.database_path, settings.starting_capital)
market = MarketData(settings)
engine = PaperEngine(settings, repository, market)
backtester = Backtester(settings, market)
static_dir = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    repository.initialize()
    task = asyncio.create_task(scheduler_loop(engine, settings, repository))
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(
    title="Multi-Coin Paper Daytrader",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class BacktestRequest(BaseModel):
    bars: int | None = Field(default=None, ge=100, le=1_000)


@app.middleware("http")
async def safety_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(static_dir / "app-icon.png", media_type="image/png")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "paper_only": settings.paper_only,
        "data_source": settings.data_source,
    }


@app.get("/api/config")
async def configuration() -> dict:
    public = settings.public_dict()
    public["paper_only_notice"] = (
        "I expose read-only GET market-data access and no real-order function."
    )
    return public


@app.get("/api/status")
async def status() -> dict:
    return {
        "paper_only": True,
        "portfolios": engine.serialize_portfolios(),
        "positions": engine.serialize_positions(),
        "markets": repository.list_markets(),
        "curves": repository.snapshot_series(),
        "trades": repository.recent_trades(),
        "events": repository.recent_events(),
    }


@app.post("/api/paper/run")
async def run_paper_cycle() -> dict:
    try:
        return await asyncio.to_thread(engine.run_once)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        repository.add_event("error", None, f"I could not complete the manual paper cycle: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest) -> dict:
    try:
        return await asyncio.to_thread(backtester.run, request.bars)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/reset")
async def reset_paper_accounts(confirm: str = Query(...)) -> dict:
    if confirm != "RESET":
        raise HTTPException(status_code=400, detail="I require confirm=RESET for this action.")
    repository.reset()
    return {
        "status": "ok",
        "message": "I reset only the local multi-coin paper accounts.",
    }
