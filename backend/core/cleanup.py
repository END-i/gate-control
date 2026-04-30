from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import SessionLocal
from models.access_log import AccessLog


async def cleanup_old_data(days: int = 30) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    media_root = Path(__file__).resolve().parents[1] / 'media'

    removed_count = 0

    async with SessionLocal() as db:
        logs_to_remove = await _find_logs_before_cutoff(db, cutoff)

        backend_root = Path(__file__).resolve().parents[1]
        media_root_resolved = media_root.resolve()
        for item in logs_to_remove:
            if item.image_path:
                try:
                    # image_path is stored relative to the backend root (e.g. "media/2024/…/uuid.jpg").
                    file_path = (backend_root / item.image_path).resolve()
                    # Guard against path-traversal: only delete files inside media_root.
                    file_path.relative_to(media_root_resolved)
                except ValueError:
                    logger.warning(
                        'Cleanup skipped image_path outside media root (possible path traversal): {}',
                        item.image_path,
                    )
                    continue
                try:
                    file_path.unlink(missing_ok=True)
                except FileNotFoundError:
                    # File may already be gone; keep cleanup idempotent.
                    pass
                except OSError as exc:
                    logger.warning('Cleanup could not delete file {}: {}', file_path, exc)

        result = await db.execute(delete(AccessLog).where(AccessLog.timestamp < cutoff))
        await db.commit()
        removed_count = result.rowcount or 0

    _remove_empty_dirs(media_root)
    logger.info('Cleanup removed {} access logs older than {} days', removed_count, days)
    return removed_count


async def _find_logs_before_cutoff(db: AsyncSession, cutoff: datetime) -> list[AccessLog]:
    result = await db.execute(select(AccessLog).where(AccessLog.timestamp < cutoff))
    return list(result.scalars().all())


def _remove_empty_dirs(root: Path) -> None:
    if not root.exists():
        return

    for path in sorted(root.rglob('*'), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                continue


async def run_cleanup_service(days: int = 30, interval_hours: int = 24) -> None:
    while True:
        try:
            await cleanup_old_data(days=days)
        except Exception as exc:
            logger.error('Cleanup service error: {}', exc)

        await asyncio.sleep(interval_hours * 3600)
