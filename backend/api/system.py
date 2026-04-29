from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from core.dependencies import get_current_admin
from core.system_status import get_last_webhook_timestamp, is_system_online
from models.admin import Admin

router = APIRouter(prefix='/system', tags=['system'])


@router.get('/status')
async def get_system_status(_: Admin = Depends(get_current_admin)) -> dict[str, object]:
    last_seen = get_last_webhook_timestamp()

    if last_seen is None:
        last_seen_iso = None
    else:
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        last_seen_iso = last_seen.isoformat().replace('+00:00', 'Z')

    return {
        'online': is_system_online(),
        'last_webhook_timestamp': last_seen_iso,
        'checked_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    }
