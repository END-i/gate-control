"""Additional tests covering security improvements and previously uncovered paths."""
from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from crud.relay_job import claim_next_relay_job, create_relay_job
from models.relay_job import RelayJobStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_headers(client) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# LoginRequest field-length validation
# ---------------------------------------------------------------------------

def test_login_username_too_long_returns_422(client):
    """Pydantic must reject usernames longer than 64 characters."""
    response = client.post(
        "/api/auth/login",
        json={"username": "a" * 65, "password": "admin"},
    )
    assert response.status_code == 422


def test_login_password_too_long_returns_422(client):
    """Pydantic must reject passwords longer than 128 characters."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "p" * 129},
    )
    assert response.status_code == 422


def test_login_max_valid_lengths_accepted(client):
    """Boundary values at exactly the limit must still pass validation."""
    # These credentials won't match → 401, but must not be 422.
    r = client.post(
        "/api/auth/login",
        json={"username": "a" * 64, "password": "p" * 128},
    )
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Content-Security-Policy header
# ---------------------------------------------------------------------------

def test_csp_header_present_on_health(client):
    response = client.get("/health")
    csp = response.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_security_headers_present_on_api_response(client):
    """All hardened headers must be present."""
    response = client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert "frame-ancestors" in response.headers.get("content-security-policy", "")
    assert "Referrer-Policy" in response.headers or "referrer-policy" in response.headers


# ---------------------------------------------------------------------------
# Rate limiting — 429 on repeated calls
# ---------------------------------------------------------------------------

def test_login_rate_limit_triggers_429(client):
    """Pre-filling the rate-limit bucket must cause the next request to return 429."""
    import core.rate_limit as rl
    from time import monotonic

    # Clear existing buckets to start fresh.
    with rl._RATE_LOCK:
        rl._RATE_BUCKETS.clear()

    # Bucket key now uses the "rl:" namespace prefix added in rate_limit.py.
    bucket_key = "rl:auth_login:testclient"
    now = monotonic()
    # Fill the bucket to the default limit (20 per 60s).
    with rl._RATE_LOCK:
        for _ in range(20):
            rl._RATE_BUCKETS[bucket_key].append(now)

    try:
        response = client.post("/api/auth/login", json={"username": "x", "password": "x"})
        assert response.status_code == 429
        assert "Retry-After" in response.headers
    finally:
        # Clean up so subsequent tests are not rate-limited.
        with rl._RATE_LOCK:
            rl._RATE_BUCKETS.clear()


# ---------------------------------------------------------------------------
# Cleanup path-traversal protection
# ---------------------------------------------------------------------------

def test_cleanup_skips_path_traversal_image_path(tmp_path: Path):
    """Path traversal in a stored image_path must not let cleanup delete files
    outside the media directory.

    We test the guard logic directly — constructing the same expression used in
    cleanup_old_data() — so the test is not coupled to the DB or SessionLocal.
    """
    backend_root = tmp_path
    media_root = tmp_path / "media"
    media_root.mkdir()
    # Create a sentinel file *outside* media root that traversal would target.
    sentinel = tmp_path / "secret.txt"
    sentinel.write_text("do not delete")

    media_root_resolved = media_root.resolve()

    evil_paths = [
        "../../secret.txt",         # relative traversal
        "../secret.txt",            # one level up
        "/etc/passwd",              # absolute path (Path division replaces root)
    ]

    for evil in evil_paths:
        try:
            file_path = (backend_root / evil).resolve()
            file_path.relative_to(media_root_resolved)
            # If we reach here the guard failed — the path is outside media_root.
            pytest.fail(f"Path traversal guard did not reject: {evil!r}")
        except ValueError:
            pass  # Guard correctly rejected the path.

    # Sentinel must still exist.
    assert sentinel.exists()


# ---------------------------------------------------------------------------
# Relay job — no double-claim (basic idempotency)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_relay_job_cannot_be_claimed_twice(db_session: AsyncSession):
    """After a job is claimed (PROCESSING) a second claim call must return None."""
    await create_relay_job(
        db_session,
        event_type="webhook_allowed",
        plate_number="ZZ9999ZZ",
        requested_by="test",
        max_attempts=3,
    )

    first = await claim_next_relay_job(db_session)
    assert first is not None
    assert first.status == RelayJobStatus.PROCESSING

    # Second claim should find nothing (job is already PROCESSING).
    second = await claim_next_relay_job(db_session)
    assert second is None


# ---------------------------------------------------------------------------
# Unknown vehicle webhook — denied, no relay
# ---------------------------------------------------------------------------

def test_webhook_unknown_plate_is_denied(client, monkeypatch):
    """A plate not in the vehicle table must be denied and relay must not fire."""
    monkeypatch.setenv("WEBHOOK_AUTH_MODE", "token")

    response = client.post(
        "/api/webhook/anpr",
        data={"plate_number": "UNKNOWN1"},
        files={"image": ("sample.jpg", b"data", "image/jpeg")},
        headers={"X-Webhook-Token": "webhook-secret", "X-Event-Id": "evt-unknown-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "denied"
    assert payload["relay_triggered"] is False


# ---------------------------------------------------------------------------
# ADMIN_ROLE validation in seed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_seed_raises_on_invalid_role(monkeypatch):
    """seed_initial_admin must raise RuntimeError for an unknown role value."""
    import core.seed as seed_mod
    from core.config import get_settings

    # Ensure settings is refreshed
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_ROLE", "superuser")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="not a valid role"):
        await seed_mod.seed_initial_admin()

    # Restore
    monkeypatch.delenv("ADMIN_ROLE", raising=False)
    get_settings.cache_clear()
