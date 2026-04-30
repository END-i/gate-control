from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.rate_limit import enforce_rate_limit
from crud.relay_job import create_relay_job
from crud.security_audit import create_security_audit_event
from core.dependencies import require_roles
from models.admin import Admin, AdminRole

router = APIRouter(prefix="/relay", tags=["relay"])


@router.post("/trigger")
async def manual_trigger(
    request: Request,
    current_admin: Admin = Depends(require_roles(AdminRole.ADMIN, AdminRole.OPERATOR)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    settings = get_settings()
    enforce_rate_limit(
        request,
        scope="relay_trigger",
        limit=settings.sensitive_rate_limit,
        window_seconds=settings.sensitive_rate_window_seconds,
    )

    item = await create_relay_job(
        db,
        event_type="manual_trigger",
        plate_number=None,
        requested_by=current_admin.username,
        max_attempts=settings.relay_worker_max_attempts,
    )

    await create_security_audit_event(
        db,
        event_type="manual_relay_trigger",
        actor=current_admin.username,
        success=True,
        details=f"Relay job queued id={item.id}",
    )

    return {"status": "accepted", "message": "relay job queued", "job_id": item.id}
