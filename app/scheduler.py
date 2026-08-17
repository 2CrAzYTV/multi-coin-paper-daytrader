from __future__ import annotations

import asyncio

from .config import Settings
from .db import Repository
from .engine import PaperEngine


async def scheduler_loop(
    engine: PaperEngine, settings: Settings, repository: Repository
) -> None:
    """Poll often, while the engine processes every closed candle only once."""
    while True:
        try:
            await asyncio.to_thread(engine.run_once)
        except Exception as exc:  # scheduler must survive remote-data failures
            repository.add_event(
                "error", None, f"I could not complete the automatic paper cycle: {exc}"
            )
        await asyncio.sleep(settings.poll_seconds)
