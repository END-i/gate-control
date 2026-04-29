from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from models.vehicle import VehicleStatus


class VehicleBase(BaseModel):
    license_plate: str = Field(min_length=3, max_length=32)
    status: VehicleStatus = VehicleStatus.BLOCKED
    owner_info: str | None = Field(default=None, max_length=255)

    @field_validator("license_plate")
    @classmethod
    def normalize_license_plate(cls, value: str) -> str:
        return value.replace(" ", "").upper()


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    license_plate: str | None = Field(default=None, min_length=3, max_length=32)
    status: VehicleStatus | None = None
    owner_info: str | None = Field(default=None, max_length=255)

    @field_validator("license_plate")
    @classmethod
    def normalize_optional_license_plate(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.replace(" ", "").upper()


class VehicleRead(BaseModel):
    id: int
    license_plate: str
    status: VehicleStatus
    owner_info: str | None

    model_config = {"from_attributes": True}


class VehicleListResponse(BaseModel):
    items: list[VehicleRead]
    total: int
    limit: int
    offset: int
