"""Unit tests for Prompt 40: Live Event Ticker — backend side."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from api.logs import _log_to_payload


# ---------------------------------------------------------------------------
# _log_to_payload helper
# ---------------------------------------------------------------------------


def _make_log(**kwargs) -> SimpleNamespace:
    defaults = dict(
        id=1,
        license_plate="ABC123",
        access_granted=True,
        image_path="media/test.jpg",
        action_type="auto_entry",
        admin_id=None,
        timestamp=datetime(2026, 5, 13, 12, 0, 0, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_log_to_payload_shape():
    log = _make_log()
    payload = _log_to_payload(log)
    assert payload["id"] == 1
    assert payload["license_plate"] == "ABC123"
    assert payload["access_granted"] is True
    assert payload["image_path"] == "media/test.jpg"
    assert "timestamp" in payload


def test_log_to_payload_timestamp_is_utc_z():
    log = _make_log(timestamp=datetime(2026, 5, 13, 12, 0, 0, tzinfo=timezone.utc))
    payload = _log_to_payload(log)
    assert payload["timestamp"].endswith("Z")


def test_log_to_payload_naive_timestamp_gets_utc():
    """Naive timestamps (no tzinfo) must be treated as UTC."""
    log = _make_log(timestamp=datetime(2026, 5, 13, 12, 0, 0))
    payload = _log_to_payload(log)
    assert payload["timestamp"].endswith("Z")


def test_log_to_payload_denied():
    log = _make_log(access_granted=False)
    payload = _log_to_payload(log)
    assert payload["access_granted"] is False


# ---------------------------------------------------------------------------
# /api/logs/stream-token endpoint (requires auth)
# ---------------------------------------------------------------------------


def test_stream_token_requires_auth(client):
    resp = client.post("/api/logs/stream-token")
    assert resp.status_code == 401


def test_stream_token_returns_token(client):
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    resp = client.post(
        "/api/logs/stream-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "sse_token" in data
    assert data["expires_in"] == 60
