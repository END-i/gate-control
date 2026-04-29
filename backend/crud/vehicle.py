from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.vehicle import Vehicle
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
    result = await db.execute(select(Vehicle).where(Vehicle.license_plate == license_plate))
    return result.scalar_one_or_none()


async def list_vehicles(db: AsyncSession, limit: int, offset: int) -> tuple[list[Vehicle], int]:
    total_result = await db.execute(select(func.count(Vehicle.id)))
    total = total_result.scalar_one()

    result = await db.execute(select(Vehicle).order_by(Vehicle.id.desc()).limit(limit).offset(offset))
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
