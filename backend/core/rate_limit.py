from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Deque

from fastapi import HTTPException, Request, status

# In-memory limiter suitable for single-instance deployment.
_RATE_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)
_RATE_LOCK = Lock()


def _client_ip(request: Request) -> str:
    if request.client is None or request.client.host is None:
        return "unknown"
    return request.client.host


def enforce_rate_limit(request: Request, scope: str, limit: int, window_seconds: int) -> None:
    if limit <= 0 or window_seconds <= 0:
        return

    now = monotonic()
    bucket_key = f"{scope}:{_client_ip(request)}"

    with _RATE_LOCK:
        bucket = _RATE_BUCKETS[bucket_key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(window_seconds)},
            )

        bucket.append(now)
