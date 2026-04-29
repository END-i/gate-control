from fastapi import APIRouter, Depends, HTTPException, status

from core.dependencies import get_current_admin
from core.hardware import trigger_relay
from models.admin import Admin

router = APIRouter(prefix="/relay", tags=["relay"])


@router.post("/trigger")
async def manual_trigger(_: Admin = Depends(get_current_admin)) -> dict[str, str]:
    success = await trigger_relay()
    if not success:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Relay trigger failed")

    return {"status": "ok", "message": "relay triggered"}
