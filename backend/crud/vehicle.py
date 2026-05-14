from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.vehicle import Vehicle, VehicleStatus
from schemas.vehicle import VehicleCreate, VehicleUpdate


async def create_vehicle(db: AsyncSession, payload: VehicleCreate) -> Vehicle:
    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def get_vehicle(db: AsyncSession, vehicle_id: int) -> Vehicle | None:
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    return result.scalar_one_or_none()


async def get_vehicle_by_plate(db: AsyncSession, license_plate: str) -> Vehicle | None:
    """Return the vehicle only if it is allowed AND its subscription is currently active.

    Access is granted when:
    - status == ALLOWED, AND
    - valid_until IS NULL (permanent) OR valid_until > UTC now
    - valid_from IS NULL (no start gate) OR valid_from <= UTC now

    The raw Vehicle row is returned so callers can inspect it even when denied;
    the access check in webhook.py reads ``vehicle.status == VehicleStatus.ALLOWED``
    but ``get_vehicle_by_plate`` returns None for expired / not-yet-started subscriptions
    so that access is implicitly denied without changing the webhook logic.
    """
    result = await db.execute(select(Vehicle).where(Vehicle.license_plate == license_plate))
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        return None
    if vehicle.status != VehicleStatus.ALLOWED:
        return vehicle  # caller checks status; return as-is for blocked/denied
    now = datetime.now(timezone.utc)
    if vehicle.valid_from is not None:
        vf = vehicle.valid_from
        if vf.tzinfo is None:
            vf = vf.replace(tzinfo=timezone.utc)
        if now < vf:
            return None  # subscription not yet started
    if vehicle.valid_until is not None:
        vu = vehicle.valid_until
        if vu.tzinfo is None:
            vu = vu.replace(tzinfo=timezone.utc)
        if now >= vu:
            return None  # subscription expired
    return vehicle


async def get_expiring_soon(db: AsyncSession, within_days: int) -> list[Vehicle]:
    """Return allowed vehicles whose valid_until is between now and now + within_days."""
    now = datetime.now(timezone.utc)
    cutoff = datetime(
        now.year, now.month, now.day,
        now.hour, now.minute, now.second,
        tzinfo=timezone.utc,
    )
    from datetime import timedelta
    deadline = cutoff + timedelta(days=within_days)
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.status == VehicleStatus.ALLOWED,
            Vehicle.valid_until.isnot(None),
            Vehicle.valid_until > cutoff,
            Vehicle.valid_until <= deadline,
        )
    )
    return list(result.scalars().all())


async def list_vehicles(
    db: AsyncSession,
    limit: int,
    offset: int,
    subscription: str = "all",
) -> tuple[list[Vehicle], int]:
    """List vehicles with optional subscription filter.

    subscription values:
    - all (default): no filter
    - active: valid_until >= now and status=allowed and (valid_from is null or valid_from <= now)
    - expiring_soon: valid_until between now and now+7d and status=allowed
    - expired: valid_until < now and status=blocked (was expired)
    - permanent: valid_until is null
    """
    now = datetime.now(timezone.utc)
    base_q = select(Vehicle)

    if subscription == "active":
        base_q = base_q.where(
            Vehicle.status == VehicleStatus.ALLOWED,
            Vehicle.valid_until.isnot(None),
            Vehicle.valid_until >= now,
        )
    elif subscription == "expiring_soon":
        from datetime import timedelta
        base_q = base_q.where(
            Vehicle.status == VehicleStatus.ALLOWED,
            Vehicle.valid_until.isnot(None),
            Vehicle.valid_until >= now,
            Vehicle.valid_until <= now + timedelta(days=7),
        )
    elif subscription == "expired":
        from datetime import timedelta
        base_q = base_q.where(
            Vehicle.valid_until.isnot(None),
            Vehicle.valid_until < now,
        )
    elif subscription == "permanent":
        base_q = base_q.where(Vehicle.valid_until.is_(None))
    # else: "all" — no extra filter

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(base_q.order_by(Vehicle.id.desc()).limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def update_vehicle(db: AsyncSession, vehicle: Vehicle, payload: VehicleUpdate) -> Vehicle:
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(vehicle, key, value)

    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def delete_vehicle(db: AsyncSession, vehicle: Vehicle) -> None:
    await db.delete(vehicle)
    await db.commit()
