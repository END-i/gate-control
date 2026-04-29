from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.dependencies import get_admin_from_token, require_roles
from core.rate_limit import enforce_rate_limit
from crud.logs import list_access_logs, list_access_logs_after_id
from models.admin import Admin, AdminRole
from models.access_log import AccessLog
from schemas.log import AccessLogListResponse

router = APIRouter(prefix="/logs", tags=["logs"])


def _log_to_payload(log: AccessLog) -> dict[str, object]:
    timestamp = log.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return {
        "id": log.id,
        "license_plate": log.license_plate,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "access_granted": log.access_granted,
        "image_path": log.image_path,
    }


@router.get("", response_model=AccessLogListResponse)
async def get_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    plate: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(require_roles(AdminRole.ADMIN, AdminRole.OPERATOR, AdminRole.VIEWER)),
) -> AccessLogListResponse:
    items, total = await list_access_logs(
        db,
        limit=limit,
        offset=offset,
        plate=plate,
        date_from=date_from,
        date_to=date_to,
    )
    return AccessLogListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/stream")
async def stream_logs(
    request: Request,
    access_token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    admin = await get_admin_from_token(access_token, db)
    if admin.role not in {AdminRole.ADMIN, AdminRole.OPERATOR, AdminRole.VIEWER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    settings = get_settings()
    enforce_rate_limit(
        request,
        scope="logs_stream",
        limit=settings.sensitive_rate_limit,
        window_seconds=settings.sensitive_rate_window_seconds,
    )

    last_id = 0

    async def event_generator():
        nonlocal last_id
        heartbeat_counter = 0
        while True:
            if await request.is_disconnected():
                break

            new_logs = await list_access_logs_after_id(db, after_id=last_id, limit=100)
            for item in new_logs:
                payload = _log_to_payload(item)
                yield f"data: {json.dumps(payload)}\\n\\n"

            if new_logs:
                last_id = new_logs[-1].id

            heartbeat_counter += 1
            if heartbeat_counter >= 15:
                yield "event: heartbeat\\ndata: {}\\n\\n"
                heartbeat_counter = 0

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
