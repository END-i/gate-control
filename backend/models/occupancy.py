from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class OccupancyState(Base):
    __tablename__ = "occupancy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    current_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
