from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ActionType(str, Enum):
    AUTO_ENTRY = "auto_entry"
    MANUAL_ENTRY = "manual_entry"


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    license_plate: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    access_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    action_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, server_default="auto_entry"
    )
    admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
