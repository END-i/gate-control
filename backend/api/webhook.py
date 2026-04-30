from __future__ import annotations

import hmac
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, Header, HTTPException, Request, UploadFile, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.rate_limit import enforce_rate_limit
from crud.access_log import create_access_log
from crud.relay_job import create_relay_job
from crud.security_audit import create_security_audit_event
from crud.webhook_event import register_webhook_event
from crud.vehicle import get_vehicle_by_plate
from models.vehicle import VehicleStatus
from core.system_status import mark_webhook_received

router = APIRouter(prefix="/webhook", tags=["webhook"])

MEDIA_ROOT = Path(__file__).resolve().parents[1] / "media"
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _verify_webhook_token(token: str | None) -> None:
    expected = get_settings().webhook_shared_secret
    if token is None or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook token")


def _parse_timestamp(value: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature") from exc

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp


def _verify_webhook_hmac(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
) -> None:
    settings = get_settings()
    if not settings.webhook_hmac_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    timestamp = _parse_timestamp(timestamp_header)
    now = datetime.now(timezone.utc)
    skew = abs((now - timestamp).total_seconds())
    if skew > settings.webhook_max_skew_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    payload = timestamp_header.encode("utf-8") + raw_body
    expected = hmac.new(
        settings.webhook_hmac_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    provided = signature_header
    if provided.startswith("sha256="):
        provided = provided.split("=", 1)[1]

    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")


async def _save_image_async(image: UploadFile) -> str:
    settings = get_settings()
    content_type = (image.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image content type")

    now = datetime.now(timezone.utc)
    day_path = MEDIA_ROOT / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    day_path.mkdir(parents=True, exist_ok=True)

    original_suffix = Path(image.filename or "upload.bin").suffix.lower()
    allowed_suffix = ALLOWED_IMAGE_CONTENT_TYPES[content_type]
    suffix = original_suffix if original_suffix in ALLOWED_IMAGE_CONTENT_TYPES.values() else allowed_suffix
    file_name = f"{uuid4().hex}{suffix}"
    destination = day_path / file_name

    content = await image.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image payload")
    if len(content) > settings.webhook_max_image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image payload is too large")

    async with aiofiles.open(destination, "wb") as output:
        await output.write(content)

    relative_path = destination.relative_to(MEDIA_ROOT.parent)
    return relative_path.as_posix()


@router.post("/anpr")
async def handle_anpr_webhook(
    request: Request,
    x_webhook_token: str | None = Header(default=None, alias="X-Webhook-Token"),
    x_webhook_timestamp: str | None = Header(default=None, alias="X-Webhook-Timestamp"),
    x_webhook_signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | bool]:
    settings = get_settings()
    await enforce_rate_limit(
        request,
        scope="webhook_anpr",
        limit=settings.webhook_rate_limit,
        window_seconds=settings.webhook_rate_window_seconds,
    )

    raw_body = await request.body()
    form = await request.form()

    event_key = request.headers.get("X-Event-Id")
    if not event_key:
        event_key = hashlib.sha256(raw_body).hexdigest()

    plate_number = form.get("plate_number")
    image = form.get("image")

    is_upload = isinstance(image, UploadFile) or (hasattr(image, "filename") and hasattr(image, "read"))
    if not isinstance(plate_number, str) or not is_upload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid multipart payload")

    if settings.webhook_auth_mode == "token":
        _verify_webhook_token(x_webhook_token)
    else:
        _verify_webhook_hmac(raw_body, x_webhook_timestamp, x_webhook_signature)

    clean_plate = plate_number.replace(" ", "").upper()
    is_new_event = await register_webhook_event(db, event_key=event_key, plate_number=clean_plate)
    if not is_new_event:
        await create_security_audit_event(
            db,
            event_type="webhook_duplicate",
            actor="anpr-webhook",
            success=True,
            details=f"Duplicate webhook skipped event_key={event_key}",
        )
        return {
            "status": "duplicate",
            "plate": clean_plate,
            "image_path": "",
            "relay_triggered": False,
        }

    image_path = await _save_image_async(image)
    mark_webhook_received()
    logger.info('Webhook received for plate {}', clean_plate)

    vehicle = await get_vehicle_by_plate(db, clean_plate)
    is_allowed = vehicle is not None and vehicle.status == VehicleStatus.ALLOWED

    await create_access_log(
        db,
        license_plate=clean_plate,
        access_granted=is_allowed,
        image_path=image_path,
    )

    relay_triggered = False
    if is_allowed:
        await create_relay_job(
            db,
            event_type="webhook_allowed",
            plate_number=clean_plate,
            requested_by="anpr-webhook",
            max_attempts=settings.relay_worker_max_attempts,
        )
        relay_triggered = True

    await create_security_audit_event(
        db,
        event_type="webhook_processed",
        actor="anpr-webhook",
        success=True,
        details=f"plate={clean_plate} granted={is_allowed} relay={relay_triggered}",
    )

    logger.info(
        'Webhook processed plate={} granted={} relay_triggered={} image_path={}',
        clean_plate,
        is_allowed,
        relay_triggered,
        image_path,
    )

    return {
        "status": "opened" if is_allowed else "denied",
        "plate": clean_plate,
        "image_path": image_path,
        "relay_triggered": relay_triggered,
    }
