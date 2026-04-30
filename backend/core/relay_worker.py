from __future__ import annotations

import asyncio
from loguru import logger

from core.config import get_settings
from core.database import SessionLocal
from core.hardware import trigger_relay
from crud.relay_job import claim_next_relay_job, mark_relay_job_failed, mark_relay_job_succeeded
from crud.security_audit import create_security_audit_event


async def run_relay_worker() -> None:
    settings = get_settings()
    poll_seconds = max(1, settings.relay_worker_poll_seconds)

    while True:
        try:
            async with SessionLocal() as db:
                item = await claim_next_relay_job(db)
                if item is None:
                    await asyncio.sleep(poll_seconds)
                    continue

                success = await trigger_relay()
                if success:
                    await mark_relay_job_succeeded(db, item)
                    await create_security_audit_event(
                        db,
                        event_type="relay_job_succeeded",
                        actor=item.requested_by,
                        success=True,
                        details=f"job_id={item.id} plate={item.plate_number or '-'} attempts={item.attempt_count}",
                    )
                    continue

                updated = await mark_relay_job_failed(
                    db,
                    item,
                    error="Relay trigger failed",
                    retry_delay_seconds=settings.relay_worker_retry_seconds,
                )
                await create_security_audit_event(
                    db,
                    event_type="relay_job_failed",
                    actor=item.requested_by,
                    success=False,
                    details=(
                        f"job_id={item.id} status={updated.status.value} "
                        f"attempts={updated.attempt_count}/{updated.max_attempts}"
                    ),
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Relay worker loop failed: {}", exc)
            await asyncio.sleep(poll_seconds)
