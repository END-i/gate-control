from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core.occupancy import occupancy_tracker

router = APIRouter(prefix="/occupancy", tags=["occupancy"])


@router.get("")
async def get_occupancy() -> dict:
    """Return current occupancy count and last-updated timestamp."""
    return occupancy_tracker.snapshot()


@router.get("/stream")
async def stream_occupancy() -> StreamingResponse:
    """SSE stream that pushes occupancy updates in real time."""

    async def event_stream():
        q = await occupancy_tracker.subscribe()
        try:
            # Send current state immediately on connect
            yield f"data: {json.dumps(occupancy_tracker.snapshot())}\n\n"
            while True:
                try:
                    snap = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield f"data: {json.dumps(snap)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            occupancy_tracker.unsubscribe(q)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
