from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import core.relay_worker as relay_worker_module
from crud.relay_job import claim_next_relay_job, create_relay_job, mark_relay_job_failed, mark_relay_job_succeeded
from models.relay_job import RelayJobStatus


@pytest.mark.asyncio
async def test_relay_job_lifecycle_success(db_session: AsyncSession) -> None:
    item = await create_relay_job(
        db_session,
        event_type='webhook_allowed',
        plate_number='AA1234BB',
        requested_by='test-suite',
        max_attempts=3,
    )

    claimed = await claim_next_relay_job(db_session)
    assert claimed is not None
    assert claimed.id == item.id
    assert claimed.status == RelayJobStatus.PROCESSING

    completed = await mark_relay_job_succeeded(db_session, claimed)
    assert completed.status == RelayJobStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_relay_job_dead_letter_after_max_attempts(db_session: AsyncSession) -> None:
    item = await create_relay_job(
        db_session,
        event_type='webhook_allowed',
        plate_number='CC5678DD',
        requested_by='test-suite',
        max_attempts=1,
    )

    claimed = await claim_next_relay_job(db_session)
    assert claimed is not None
    assert claimed.id == item.id

    failed = await mark_relay_job_failed(db_session, claimed, error='boom', retry_delay_seconds=1)
    assert failed.status == RelayJobStatus.DEAD_LETTER
    assert failed.attempt_count == 1


@pytest.mark.asyncio
async def test_relay_job_retry_when_attempts_remain(db_session: AsyncSession) -> None:
    item = await create_relay_job(
        db_session,
        event_type='manual_trigger',
        plate_number=None,
        requested_by='tester',
        max_attempts=3,
    )

    claimed = await claim_next_relay_job(db_session)
    assert claimed is not None
    assert claimed.id == item.id

    failed = await mark_relay_job_failed(db_session, claimed, error='temporary', retry_delay_seconds=2)
    assert failed.status == RelayJobStatus.PENDING
    assert failed.attempt_count == 1
    assert failed.last_error == 'temporary'


def test_relay_worker_symbol_exists() -> None:
    assert callable(relay_worker_module.run_relay_worker)
