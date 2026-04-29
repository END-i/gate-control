from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models.security_audit import SecurityAudit


async def create_security_audit_event(
    db: AsyncSession,
    event_type: str,
    actor: str,
    success: bool,
    details: str,
) -> SecurityAudit:
    event = SecurityAudit(
        event_type=event_type,
        actor=actor,
        success=success,
        details=details,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
