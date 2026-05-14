"""Backup / Restore API for Vehicle records.

GET  /api/backup/export  — export all vehicles as JSON array
POST /api/backup/import  — clear vehicles table, insert restored records,
                           rebuild camera whitelist via karsun_api
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import require_roles
from core.karsun_api import sync_vehicle_to_camera
from crud.vehicle import list_vehicles
from models.admin import Admin, AdminRole
from models.vehicle import Vehicle, VehicleStatus
from schemas.vehicle import VehicleRead

router = APIRouter(prefix="/backup", tags=["backup"])


class VehicleImportItem(BaseModel):
    license_plate: str = Field(min_length=3, max_length=32)
    status: VehicleStatus = VehicleStatus.BLOCKED
    owner_info: str | None = Field(default=None, max_length=255)

    @field_validator("license_plate")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.replace(" ", "").upper()


class ImportResponse(BaseModel):
    restored: int
    camera_synced: int


@router.get("/export", response_model=list[VehicleRead])
async def export_vehicles(
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(require_roles(AdminRole.ADMIN, AdminRole.OPERATOR)),
) -> list[VehicleRead]:
    """Export all vehicle records as a JSON array."""
    # Fetch all without pagination limit
    items, _total = await list_vehicles(db, limit=100_000, offset=0)
    return [VehicleRead.model_validate(v) for v in items]


@router.post("/import", response_model=ImportResponse, status_code=status.HTTP_200_OK)
async def import_vehicles(
    payload: list[VehicleImportItem],
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(require_roles(AdminRole.ADMIN)),
) -> ImportResponse:
    """Clear vehicles table, insert restored records, rebuild camera whitelist.

    Only admins may import (destructive operation).
    """
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty import payload")

    # Clear existing vehicles
    await db.execute(delete(Vehicle))
    await db.commit()

    # Insert restored records
    new_vehicles: list[Vehicle] = []
    seen_plates: set[str] = set()
    for item in payload:
        if item.license_plate in seen_plates:
            continue  # skip duplicates within the import payload
        seen_plates.add(item.license_plate)
        v = Vehicle(
            license_plate=item.license_plate,
            status=item.status,
            owner_info=item.owner_info,
        )
        db.add(v)
        new_vehicles.append(v)

    await db.commit()

    # Rebuild camera whitelist
    synced = 0
    for v in new_vehicles:
        ok = await sync_vehicle_to_camera(v.license_plate, v.status)
        if ok:
            synced += 1

    return ImportResponse(restored=len(new_vehicles), camera_synced=synced)
