from __future__ import annotations

from datetime import datetime, timezone

_last_webhook_timestamp: datetime | None = None


def mark_webhook_received(timestamp: datetime | None = None) -> None:
    global _last_webhook_timestamp
    _last_webhook_timestamp = timestamp or datetime.now(timezone.utc)


def get_last_webhook_timestamp() -> datetime | None:
    return _last_webhook_timestamp


def is_system_online(max_age_seconds: int = 60) -> bool:
    if _last_webhook_timestamp is None:
        return False

    age = datetime.now(timezone.utc) - _last_webhook_timestamp
    return age.total_seconds() <= max_age_seconds
