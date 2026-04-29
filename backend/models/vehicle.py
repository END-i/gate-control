from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class VehicleStatus(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    license_plate: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(VehicleStatus, name="vehicle_status"),
        default=VehicleStatus.BLOCKED,
        nullable=False,
    )
    owner_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
