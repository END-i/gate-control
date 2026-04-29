from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AccessLogRead(BaseModel):
    id: int
    license_plate: str
    timestamp: datetime
    access_granted: bool
    image_path: str | None

    model_config = {"from_attributes": True}


class AccessLogListResponse(BaseModel):
    items: list[AccessLogRead]
    total: int
    limit: int
    offset: int
