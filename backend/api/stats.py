from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_admin
from crud.stats import get_stats
from models.admin import Admin
from schemas.stats import StatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def read_stats(
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> StatsResponse:
    data = await get_stats(db)
    return StatsResponse(**data)
