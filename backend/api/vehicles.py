from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_admin
from crud.vehicle import (
    create_vehicle,
    delete_vehicle,
    get_vehicle,
    get_vehicle_by_plate,
    list_vehicles,
    update_vehicle,
)
from models.admin import Admin
from schemas.vehicle import VehicleCreate, VehicleListResponse, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=VehicleListResponse)
async def get_vehicles(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> VehicleListResponse:
    items, total = await list_vehicles(db, limit=limit, offset=offset)
    return VehicleListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def post_vehicle(
    payload: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> VehicleRead:
    existing = await get_vehicle_by_plate(db, payload.license_plate)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle already exists")

    vehicle = await create_vehicle(db, payload)
    return VehicleRead.model_validate(vehicle)


@router.put("/{vehicle_id}", response_model=VehicleRead)
async def put_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> VehicleRead:
    vehicle = await get_vehicle(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    if payload.license_plate and payload.license_plate != vehicle.license_plate:
        duplicate = await get_vehicle_by_plate(db, payload.license_plate)
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle already exists")

    updated = await update_vehicle(db, vehicle, payload)
    return VehicleRead.model_validate(updated)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> None:
    vehicle = await get_vehicle(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    await delete_vehicle(db, vehicle)
