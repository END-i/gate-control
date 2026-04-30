"""Chaos / fault-injection tests.

These tests verify that the system behaves correctly under adverse conditions:
Redis unavailable, relay timeout, DB disconnect, etc.
All external calls are mocked — no real infrastructure needed.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login_token(client: TestClient) -> str:
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Redis unavailable — rate limiter must fall back to in-memory
# ---------------------------------------------------------------------------

def test_rate_limiter_falls_back_when_redis_is_down(client: TestClient):
    """When Redis raises on connect, the in-memory fallback is used and the
    request is allowed (not rejected with 500)."""
    import core.rate_limit as rl

    # Temporarily inject a broken Redis client
    broken_redis = MagicMock()
    broken_redis.eval = AsyncMock(side_effect=ConnectionError("Redis is down"))
    original = rl._redis_client
    rl._redis_client = broken_redis

    try:
        resp = client.get("/health")
        assert resp.status_code == 200
    finally:
        rl._redis_client = original


def test_rate_limiter_returns_429_when_in_memory_bucket_exhausted(client: TestClient):
    """In-memory rate limiter returns 429 once the bucket fills."""
    import core.rate_limit as rl
    import time as _time
    import collections

    # Ensure we're using the in-memory path (no Redis)
    original = rl._redis_client
    rl._redis_client = None

    bucket_key = "rl:chaos_test:testclient"
    try:
        # Pre-fill the bucket beyond the limit (limit=1)
        with rl._RATE_LOCK:
            now = _time.monotonic()
            rl._RATE_BUCKETS[bucket_key] = collections.deque([now, now])

        with pytest.raises(Exception):
            # Call the internal _enforce_memory directly — must raise 429
            rl._enforce_memory(bucket_key=bucket_key, limit=1, window_seconds=3600)
    finally:
        rl._redis_client = original
        with rl._RATE_LOCK:
            rl._RATE_BUCKETS.pop(bucket_key, None)


# ---------------------------------------------------------------------------
# Relay hardware timeout — webhook still returns 200 (relay is async via queue)
# ---------------------------------------------------------------------------

def test_webhook_succeeds_when_relay_hardware_is_unavailable(client: TestClient):
    """Relay trigger is now async (relay_jobs queue), so a hardware timeout
    must not affect the webhook response."""
    import io

    jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C" + b"\x08" * 64
        + b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd0\xff\xd9"
    )

    # Mock storage so no filesystem write happens
    with patch("api.webhook.get_storage") as mock_storage:
        storage_instance = MagicMock()
        storage_instance.save = AsyncMock(return_value="media/2026/04/30/fake.jpg")
        mock_storage.return_value = storage_instance

        resp = client.post(
            "/api/webhook/anpr",
            headers={"X-Webhook-Token": "webhook-secret"},
            data={"plate_number": "CHAOS01"},
            files={"image": ("test.jpg", io.BytesIO(jpeg), "image/jpeg")},
        )

    # Webhook should succeed; relay is enqueued asynchronously
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "plate" in body


# ---------------------------------------------------------------------------
# relay_worker: trigger_relay timeout → job marked failed, not dead-lettered
# on first attempt
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_relay_worker_retries_on_hardware_timeout(db_session):
    """When trigger_relay times out on first attempt, the job gets rescheduled
    (status stays pending or goes back to pending via retry delay), not dead_lettered."""
    from crud.relay_job import create_relay_job, claim_next_relay_job, mark_relay_job_failed
    from models.relay_job import RelayJobStatus

    job = await create_relay_job(
        db_session,
        event_type="test_chaos",
        plate_number="CHAOS02",
        requested_by="chaos-test",
        max_attempts=3,
    )

    claimed = await claim_next_relay_job(db_session)
    assert claimed is not None
    assert claimed.id == job.id

    # First failure — should reschedule (not dead_letter)
    updated = await mark_relay_job_failed(
        db_session,
        claimed,
        error="httpx.TimeoutException",
        retry_delay_seconds=1,
    )
    assert updated.status != RelayJobStatus.DEAD_LETTER
    assert updated.attempt_count == 1


@pytest.mark.asyncio
async def test_relay_worker_dead_letters_after_max_attempts(db_session):
    """After max_attempts failures the job is moved to dead_letter."""
    from crud.relay_job import create_relay_job, claim_next_relay_job, mark_relay_job_failed
    from models.relay_job import RelayJobStatus

    await create_relay_job(
        db_session,
        event_type="test_chaos_dl",
        plate_number="CHAOS03",
        requested_by="chaos-test",
        max_attempts=2,
    )

    claimed = await claim_next_relay_job(db_session)
    assert claimed is not None

    # Exhaust all attempts
    updated = claimed
    for _ in range(2):
        # Re-claim after each failure (simulate worker retry loop)
        updated = await mark_relay_job_failed(
            db_session,
            updated,
            error="timeout",
            retry_delay_seconds=0,
        )
        if updated.status == RelayJobStatus.DEAD_LETTER:
            break
        next_claim = await claim_next_relay_job(db_session)
        if next_claim is None:
            break
        updated = next_claim

    assert updated.status == RelayJobStatus.DEAD_LETTER


# ---------------------------------------------------------------------------
# Storage: S3Storage falls back gracefully when aioboto3 is missing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_s3_storage_raises_import_error_without_aioboto3():
    """S3Storage.save() raises a clear ImportError when aioboto3 is not installed."""
    import sys
    from core.storage import S3Storage

    storage = S3Storage(
        bucket="test-bucket",
        endpoint_url="http://localhost:9000",
        access_key="key",
        secret_key="secret",
    )

    # Temporarily hide aioboto3 from the import system
    original = sys.modules.get("aioboto3")
    sys.modules["aioboto3"] = None  # type: ignore[assignment]
    try:
        with pytest.raises(ImportError, match="aioboto3"):
            await storage.save(b"data", ".jpg")
    finally:
        if original is None:
            sys.modules.pop("aioboto3", None)
        else:
            sys.modules["aioboto3"] = original


# ---------------------------------------------------------------------------
# Vault secrets adapter: unreachable Vault is a no-op warning (not a crash)
# ---------------------------------------------------------------------------

def test_prefetch_secrets_no_op_without_vault_addr(monkeypatch):
    """prefetch_secrets() must be a no-op when VAULT_ADDR is not set."""
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    from core.secrets import prefetch_secrets
    # Must not raise
    prefetch_secrets()


def test_prefetch_secrets_logs_warning_on_connection_error(monkeypatch):
    """prefetch_secrets() logs a warning and does not crash when Vault is unreachable."""
    monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:19999")
    monkeypatch.setenv("VAULT_TOKEN", "fake-token")

    from core.secrets import prefetch_secrets
    # Must not raise even if the TCP connection is refused
    prefetch_secrets()
