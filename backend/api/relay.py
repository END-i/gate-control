from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.hardware import trigger_relay
from core.rate_limit import enforce_rate_limit
from crud.security_audit import create_security_audit_event
from core.dependencies import require_roles
from models.admin import Admin, AdminRole

router = APIRouter(prefix="/relay", tags=["relay"])


@router.post("/trigger")
async def manual_trigger(
    request: Request,
    current_admin: Admin = Depends(require_roles(AdminRole.ADMIN, AdminRole.OPERATOR)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    settings = get_settings()
    enforce_rate_limit(
        request,
        scope="relay_trigger",
        limit=settings.sensitive_rate_limit,
        window_seconds=settings.sensitive_rate_window_seconds,
    )

    success = await trigger_relay()
    if not success:
        await create_security_audit_event(
            db,
            event_type="manual_relay_trigger",
            actor=current_admin.username,
            success=False,
            details="Relay trigger failed",
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Relay trigger failed")

    await create_security_audit_event(
        db,
        event_type="manual_relay_trigger",
        actor=current_admin.username,
        success=True,
        details="Relay trigger executed",
    )

    return {"status": "ok", "message": "relay triggered"}
