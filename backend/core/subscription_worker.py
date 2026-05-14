"""Subscription expiry background worker.

Runs on a configurable interval. Finds allowed vehicles whose valid_until is
in the past, marks them blocked, and emits a security_audit event for each.
The task is idempotent and safe to run concurrently.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from core.config import get_settings
from core.database import SessionLocal
from core.shutdown import is_shutting_down
from crud.security_audit import create_security_audit_event
from models.vehicle import Vehicle, VehicleStatus


async def run_subscription_expiry_worker() -> None:
    settings = get_settings()
    interval = max(10, settings.subscription_expiry_check_interval_seconds)

    while not is_shutting_down():
        try:
            await _check_and_expire()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("subscription_expiry_worker error: {}", exc)
        await asyncio.sleep(interval)


async def _check_and_expire() -> int:
    """Expire overdue allowed vehicles.  Returns number of vehicles expired."""
    now = datetime.now(timezone.utc)
    expired_count = 0

    async with SessionLocal() as db:
        result = await db.execute(
            select(Vehicle).where(
                Vehicle.status == VehicleStatus.ALLOWED,
                Vehicle.valid_until.isnot(None),
                Vehicle.valid_until < now,
            )
        )
        vehicles = list(result.scalars().all())

        for vehicle in vehicles:
            vehicle.status = VehicleStatus.BLOCKED
            await create_security_audit_event(
                db,
                event_type="subscription_expired",
                actor="subscription-worker",
                success=True,
                details=(
                    f"plate_number={vehicle.license_plate} "
                    f"valid_until={vehicle.valid_until.isoformat() if vehicle.valid_until else 'null'}"
                ),
            )
            logger.info(
                "Subscription expired: plate={} valid_until={}",
                vehicle.license_plate,
                vehicle.valid_until,
            )
            expired_count += 1

        if vehicles:
            await db.commit()

    return expired_count
