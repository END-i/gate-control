"""Unit tests for LocalStorage.move_to_cold retention helper."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from core.storage import LocalStorage


@pytest.fixture()
def media_root(tmp_path: Path) -> Path:
    return tmp_path / "media"


def _make_file(root: Path, year: int, month: int, day: int, name: str = "img.jpg") -> Path:
    d = root / f"{year:04d}" / f"{month:02d}" / f"{day:02d}"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_bytes(b"\xff\xd8\xff\xd9")  # minimal JPEG marker
    return p


def test_move_to_cold_moves_old_files(media_root: Path):
    """Files older than hot_days must be moved into the cold/ sub-tree."""
    storage = LocalStorage(media_root=media_root)
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=40)
    recent = now - timedelta(days=5)

    old_file = _make_file(media_root, old.year, old.month, old.day, "old.jpg")
    recent_file = _make_file(media_root, recent.year, recent.month, recent.day, "recent.jpg")

    moved = storage.move_to_cold(hot_days=30)

    assert moved == 1
    assert not old_file.exists()
    cold_path = (
        media_root / "cold" / f"{old.year:04d}" / f"{old.month:02d}" / f"{old.day:02d}" / "old.jpg"
    )
    assert cold_path.exists()
    assert recent_file.exists()  # untouched


def test_move_to_cold_nothing_when_all_recent(media_root: Path):
    """Nothing is moved when all files are within the hot window."""
    storage = LocalStorage(media_root=media_root)
    now = datetime.now(timezone.utc)
    _make_file(media_root, now.year, now.month, now.day, "today.jpg")

    moved = storage.move_to_cold(hot_days=30)
    assert moved == 0


def test_move_to_cold_skips_cold_subdir_itself(media_root: Path):
    """The cold/ directory must not be traversed as a source."""
    storage = LocalStorage(media_root=media_root)
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=40)

    # Put a file directly into the cold sub-tree (simulating prior run)
    _make_file(media_root / "cold", old.year, old.month, old.day, "already_cold.jpg")

    moved = storage.move_to_cold(hot_days=30)
    assert moved == 0  # must not double-move


def test_move_to_cold_empty_root(media_root: Path):
    """move_to_cold on a non-existent / empty media root returns 0 without error."""
    storage = LocalStorage(media_root=media_root)
    # media_root does not exist yet
    if not media_root.exists():
        media_root.mkdir(parents=True)
    assert storage.move_to_cold(hot_days=30) == 0
