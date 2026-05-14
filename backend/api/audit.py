from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import require_roles
from models.admin import Admin, AdminRole
from models.security_audit import SecurityAudit

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None),
    actor: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(require_roles(AdminRole.ADMIN)),
) -> dict:
    q = select(SecurityAudit)
    count_q = select(func.count()).select_from(SecurityAudit)

    if event_type:
        q = q.where(SecurityAudit.event_type == event_type)
        count_q = count_q.where(SecurityAudit.event_type == event_type)
    if actor:
        q = q.where(SecurityAudit.actor == actor)
        count_q = count_q.where(SecurityAudit.actor == actor)
    if date_from:
        q = q.where(SecurityAudit.timestamp >= date_from)
        count_q = count_q.where(SecurityAudit.timestamp >= date_from)
    if date_to:
        q = q.where(SecurityAudit.timestamp <= date_to)
        count_q = count_q.where(SecurityAudit.timestamp <= date_to)

    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    q = q.order_by(SecurityAudit.timestamp.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "actor": e.actor,
                "success": e.success,
                "details": e.details,
                "timestamp": e.timestamp.isoformat().replace("+00:00", "Z"),
            }
            for e in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
