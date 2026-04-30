"""Media storage abstraction.

Provides two backends, selected via the ``MEDIA_STORAGE_BACKEND`` env var:

``local`` (default)
    Saves files to ``backend/media/YYYY/MM/DD/<uuid>.<ext>``.
    No extra dependencies.

``s3``
    Saves files to an S3-compatible object store (AWS S3, MinIO, etc.).
    Requires ``aioboto3`` to be installed (``pip install aioboto3``).
    Configure via env vars:
      - ``S3_BUCKET``            (required)
      - ``S3_ENDPOINT_URL``      (required for MinIO; omit for AWS)
      - ``AWS_ACCESS_KEY_ID``    (required)
      - ``AWS_SECRET_ACCESS_KEY``(required)
      - ``S3_PUBLIC_BASE_URL``   optional; used to construct the public URL
                                 returned in the ``image_path`` column.
                                 Falls back to ``<endpoint>/<bucket>``.

Usage::

    from core.storage import get_storage

    storage = get_storage()
    path = await storage.save(content=raw_bytes, suffix=".jpg")
    # path is stored in AccessLog.image_path
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import aiofiles


class MediaStorage(ABC):
    """Abstract base for all media storage backends."""

    @abstractmethod
    async def save(self, content: bytes, suffix: str) -> str:
        """Persist *content* and return a stable path/key string.

        The returned string is stored in ``AccessLog.image_path``.
        For local storage it is a relative POSIX path (``media/YYYY/MM/DD/file.jpg``).
        For S3 it is the object key (``media/YYYY/MM/DD/file.jpg``).
        """

    @abstractmethod
    async def url(self, path: str) -> str:
        """Resolve *path* to an absolute URL suitable for browser consumption."""


# ---------------------------------------------------------------------------
# Local (default) backend
# ---------------------------------------------------------------------------

class LocalStorage(MediaStorage):
    """Stores files on the local filesystem under *media_root*."""

    def __init__(self, media_root: Path) -> None:
        self._root = media_root

    async def save(self, content: bytes, suffix: str) -> str:
        now = datetime.now(timezone.utc)
        day_path = self._root / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        day_path.mkdir(parents=True, exist_ok=True)
        file_name = f"{uuid4().hex}{suffix}"
        destination = day_path / file_name
        async with aiofiles.open(destination, "wb") as fh:
            await fh.write(content)
        return destination.relative_to(self._root.parent).as_posix()

    async def url(self, path: str) -> str:
        return f"/{path}"


# ---------------------------------------------------------------------------
# S3-compatible backend
# ---------------------------------------------------------------------------

class S3Storage(MediaStorage):
    """Stores files in an S3-compatible object store (AWS S3, MinIO, …).

    Requires ``aioboto3`` (``pip install aioboto3``).
    """

    def __init__(
        self,
        bucket: str,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        public_base_url: str = "",
    ) -> None:
        self._bucket = bucket
        self._endpoint_url = endpoint_url or None
        self._access_key = access_key
        self._secret_key = secret_key
        self._public_base_url = public_base_url.rstrip("/")

    def _key(self, suffix: str) -> str:
        now = datetime.now(timezone.utc)
        return f"media/{now.strftime('%Y/%m/%d')}/{uuid4().hex}{suffix}"

    async def save(self, content: bytes, suffix: str) -> str:
        try:
            import aioboto3  # optional dependency
        except ImportError as exc:
            raise ImportError(
                "S3 storage backend requires aioboto3. "
                "Install it with: pip install aioboto3"
            ) from exc

        key = self._key(suffix)
        session = aioboto3.Session(
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
        )
        async with session.client(
            "s3",
            endpoint_url=self._endpoint_url,
        ) as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content,
                ContentType=_suffix_to_content_type(suffix),
            )
        return key

    async def url(self, path: str) -> str:
        if self._public_base_url:
            return f"{self._public_base_url}/{path}"
        base = self._endpoint_url or "https://s3.amazonaws.com"
        return f"{base.rstrip('/')}/{self._bucket}/{path}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_storage() -> MediaStorage:
    """Return the configured media storage backend.

    Reads ``MEDIA_STORAGE_BACKEND`` (``local`` or ``s3``) from Settings.
    """
    from core.config import get_settings  # avoid circular import at module load

    settings = get_settings()
    if settings.media_storage_backend == "s3":
        return S3Storage(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint_url,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
            public_base_url=settings.s3_public_base_url,
        )
    # default: local
    media_root = Path(__file__).resolve().parents[1] / "media"
    return LocalStorage(media_root=media_root)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _suffix_to_content_type(suffix: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(suffix.lower(), "application/octet-stream")
