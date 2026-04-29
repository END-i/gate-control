from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.webhook_event import WebhookEvent


async def register_webhook_event(
    db: AsyncSession,
    event_key: str,
    plate_number: str,
) -> bool:
    item = WebhookEvent(event_key=event_key, plate_number=plate_number)
    db.add(item)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return False

    return True
