from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.karsun_api import trigger_relay as karsun_trigger_relay
from core.rate_limit import enforce_rate_limit
from crud.access_log import create_access_log
from crud.security_audit import create_security_audit_event
from core.dependencies import require_roles
from models.admin import Admin, AdminRole

router = APIRouter(prefix="/relay", tags=["relay"])


async def _do_manual_open(
    request: Request,
    current_admin: Admin,
    db: AsyncSession,
) -> dict[str, object]:
    settings = get_settings()
    await enforce_rate_limit(
        request,
        scope="relay_trigger",
        limit=settings.sensitive_rate_limit,
        window_seconds=settings.sensitive_rate_window_seconds,
    )

    opened = await karsun_trigger_relay()

    await create_access_log(
        db,
        license_plate="MANUAL",
        access_granted=opened,
        image_path=None,
        action_type="manual_entry",
        admin_id=current_admin.id,
    )

    await create_security_audit_event(
        db,
        event_type="manual_relay_trigger",
        actor=current_admin.username,
        success=opened,
        details=f"karsun_relay_result={opened}",
    )

    if opened:
        return {"status": "opened"}
    return {"status": "error", "detail": "camera unreachable"}


@router.post("/manual_open")
async def manual_open(
    request: Request,
    current_admin: Admin = Depends(require_roles(AdminRole.ADMIN, AdminRole.OPERATOR)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    return await _do_manual_open(request, current_admin, db)


@router.post("/trigger", deprecated=True)
async def manual_trigger(
    request: Request,
    current_admin: Admin = Depends(require_roles(AdminRole.ADMIN, AdminRole.OPERATOR)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Deprecated alias for /api/relay/manual_open \u2014 kept for backward compatibility."""
    return await _do_manual_open(request, current_admin, db)
