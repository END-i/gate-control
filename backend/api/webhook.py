from __future__ import annotations

import hmac
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request, UploadFile, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import FormData, UploadFile as StarletteUploadFile

from core.config import get_settings
from core.database import get_db
from core.rate_limit import enforce_rate_limit
from core.storage import get_storage
from crud.access_log import create_access_log
from crud.relay_job import create_relay_job
from crud.security_audit import create_security_audit_event
from crud.webhook_event import register_webhook_event
from crud.vehicle import get_vehicle_by_plate
from models.vehicle import VehicleStatus
from core.system_status import mark_webhook_received

router = APIRouter(prefix="/webhook", tags=["webhook"])

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

INVALID_WEBHOOK_SIGNATURE = "Invalid webhook signature"
INVALID_MULTIPART_PAYLOAD = "Invalid multipart payload"
INVALID_PLATE_NUMBER = "Invalid plate number"
# Restrict header-supplied event keys to a bounded safe character set before storing them.
EVENT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
PLATE_NUMBER_PATTERN = re.compile(r"^[A-Z0-9-]{3,32}$")


def _verify_webhook_token(token: str | None) -> None:
    expected = get_settings().webhook_shared_secret
    if token is None or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook token")


def _parse_timestamp(value: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_WEBHOOK_SIGNATURE) from exc

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp


def _require_webhook_signature_headers(timestamp_header: str | None, signature_header: str | None) -> tuple[str, str]:
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_WEBHOOK_SIGNATURE)
    return timestamp_header, signature_header


def _validate_timestamp_skew(timestamp: datetime, max_skew_seconds: int) -> None:
    now = datetime.now(timezone.utc)
    skew = abs((now - timestamp).total_seconds())
    if skew > max_skew_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_WEBHOOK_SIGNATURE)


def _build_webhook_signature(secret: str, timestamp_header: str, raw_body: bytes) -> str:
    payload = timestamp_header.encode("utf-8") + raw_body
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _normalize_signature(signature_header: str) -> str:
    normalized = signature_header.split("=", 1)[1] if signature_header.startswith("sha256=") else signature_header
    if not SHA256_HEX_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_WEBHOOK_SIGNATURE)
    return normalized


def _verify_webhook_hmac(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
) -> None:
    settings = get_settings()
    if not settings.webhook_hmac_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_WEBHOOK_SIGNATURE)

    safe_timestamp, safe_signature = _require_webhook_signature_headers(timestamp_header, signature_header)
    timestamp = _parse_timestamp(safe_timestamp)
    _validate_timestamp_skew(timestamp, settings.webhook_max_skew_seconds)
    expected = _build_webhook_signature(settings.webhook_hmac_secret, safe_timestamp, raw_body)
    provided = _normalize_signature(safe_signature)
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_WEBHOOK_SIGNATURE)


def _extract_event_key(raw_body: bytes, event_id_header: str | None) -> str:
    if event_id_header and EVENT_KEY_PATTERN.fullmatch(event_id_header):
        return event_id_header
    return hashlib.sha256(raw_body).hexdigest()


def _extract_plate_and_image(form: FormData) -> tuple[str, UploadFile]:
    plate_number = form.get("plate_number") or form.get("plateNumber")
    image = form.get("image") or form.get("plateImage")
    # `request.form()` may surface Starlette's UploadFile while FastAPI re-exports its own subclass.
    is_upload = isinstance(image, (UploadFile, StarletteUploadFile))
    if not isinstance(plate_number, str) or not is_upload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_MULTIPART_PAYLOAD)
    return plate_number, cast(UploadFile, image)


def _normalize_plate_number(plate_number: str) -> str:
    normalized = plate_number.replace(" ", "").upper()
    if not PLATE_NUMBER_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_PLATE_NUMBER)
    return normalized


def _verify_webhook_auth(
    auth_mode: str,
    raw_body: bytes,
    x_webhook_token: str | None,
    x_webhook_timestamp: str | None,
    x_webhook_signature: str | None,
) -> None:
    if auth_mode == "token":
        _verify_webhook_token(x_webhook_token)
        return
    _verify_webhook_hmac(raw_body, x_webhook_timestamp, x_webhook_signature)


async def _save_image_async(image: UploadFile) -> str:
    settings = get_settings()
    content_type = (image.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image content type")

    content = await image.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image payload")
    if len(content) > settings.webhook_max_image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image payload is too large")

    original_suffix = Path(image.filename or "upload.bin").suffix.lower()
    allowed_suffix = ALLOWED_IMAGE_CONTENT_TYPES[content_type]
    suffix = original_suffix if original_suffix in ALLOWED_IMAGE_CONTENT_TYPES.values() else allowed_suffix

    storage = get_storage()
    return await storage.save(content=content, suffix=suffix)


async def _handle_duplicate_event(db: AsyncSession, event_key: str, clean_plate: str) -> dict[str, str | bool]:
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


async def _is_allowed_vehicle(db: AsyncSession, clean_plate: str) -> bool:
    vehicle = await get_vehicle_by_plate(db, clean_plate)
    return vehicle is not None and vehicle.status == VehicleStatus.ALLOWED


async def _create_access_entry(
    db: AsyncSession,
    clean_plate: str,
    image_path: str,
) -> bool:
    is_allowed = await _is_allowed_vehicle(db, clean_plate)
    await create_access_log(
        db,
        license_plate=clean_plate,
        access_granted=is_allowed,
        image_path=image_path,
    )
    return is_allowed


async def _queue_relay_job_if_allowed(
    db: AsyncSession,
    clean_plate: str,
    is_allowed: bool,
    relay_worker_max_attempts: int,
) -> bool:
    if not is_allowed:
        return False
    await create_relay_job(
        db,
        event_type="webhook_allowed",
        plate_number=clean_plate,
        requested_by="anpr-webhook",
        max_attempts=relay_worker_max_attempts,
    )
    return True


async def _record_processed_event(
    db: AsyncSession,
    clean_plate: str,
    is_allowed: bool,
    relay_triggered: bool,
) -> None:
    await create_security_audit_event(
        db,
        event_type="webhook_processed",
        actor="anpr-webhook",
        success=True,
        details=f"plate={clean_plate} granted={is_allowed} relay={relay_triggered}",
    )


def _build_webhook_response(clean_plate: str, image_path: str, is_allowed: bool, relay_triggered: bool) -> dict[str, str | bool]:
    return {
        "status": "opened" if is_allowed else "denied",
        "plate": clean_plate,
        "image_path": image_path,
        "relay_triggered": relay_triggered,
    }


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
    event_key = _extract_event_key(raw_body, request.headers.get("X-Event-Id"))
    plate_number, image = _extract_plate_and_image(form)
    _verify_webhook_auth(
        settings.webhook_auth_mode,
        raw_body,
        x_webhook_token,
        x_webhook_timestamp,
        x_webhook_signature,
    )

    clean_plate = _normalize_plate_number(plate_number)
    is_new_event = await register_webhook_event(db, event_key=event_key, plate_number=clean_plate)
    if not is_new_event:
        return await _handle_duplicate_event(db, event_key, clean_plate)

    image_path = await _save_image_async(image)
    mark_webhook_received()
    logger.info('Webhook received for plate {}', clean_plate)

    is_allowed = await _create_access_entry(db, clean_plate, image_path)
    relay_triggered = await _queue_relay_job_if_allowed(
        db,
        clean_plate,
        is_allowed,
        settings.relay_worker_max_attempts,
    )
    await _record_processed_event(db, clean_plate, is_allowed, relay_triggered)

    logger.info(
        'Webhook processed plate={} granted={} relay_triggered={} image_path={}',
        clean_plate,
        is_allowed,
        relay_triggered,
        image_path,
    )

    return _build_webhook_response(clean_plate, image_path, is_allowed, relay_triggered)
