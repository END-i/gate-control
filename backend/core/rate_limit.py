"""Rate-limiting middleware.

Backends
--------
* **Redis** (recommended for production / multi-replica):
  Set ``REDIS_URL`` in the environment (e.g. ``redis://localhost:6379/0``).
  Uses an atomic Lua sliding-window counter — safe under concurrent workers.

* **In-memory** (default, single-instance dev / test):
  Thread-safe sliding-window per-IP bucket.  Resets on restart and does NOT
  work across workers or replicas.

Trusted proxies
---------------
Set ``TRUSTED_PROXY_IPS`` to a comma-separated list of reverse-proxy IPs
(e.g. ``127.0.0.1,10.0.0.1``) to honour ``X-Real-IP`` / ``X-Forwarded-For``.
"""
from __future__ import annotations

import random
import time
from collections import defaultdict, deque
from threading import Lock
from typing import TYPE_CHECKING, Deque

from fastapi import HTTPException, Request, status
from loguru import logger

if TYPE_CHECKING:
    import redis.asyncio as aioredis

# ---------------------------------------------------------------------------
# Trusted-proxy IP set (populated at first use from Settings)
# ---------------------------------------------------------------------------
_trusted_proxy_ips: frozenset[str] | None = None


def _get_trusted_proxy_ips() -> frozenset[str]:
    global _trusted_proxy_ips
    if _trusted_proxy_ips is None:
        from core.config import get_settings
        raw = get_settings().trusted_proxy_ips
        _trusted_proxy_ips = frozenset(ip.strip() for ip in raw.split(",") if ip.strip())
    return _trusted_proxy_ips


def _client_ip(request: Request) -> str:
    direct_host = request.client.host if request.client else None
    if direct_host and direct_host in _get_trusted_proxy_ips():
        x_real_ip = request.headers.get("X-Real-IP", "").strip()
        if x_real_ip:
            return x_real_ip
        xff = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if xff:
            return xff
    return direct_host or "unknown"


# ---------------------------------------------------------------------------
# Redis backend
# ---------------------------------------------------------------------------
_redis_client: "aioredis.Redis | None" = None
_redis_init_done = False

# Atomic Lua sliding-window: returns 1 if allowed, 0 if rate-limited.
_LUA_SLIDING_WINDOW = """
local key         = KEYS[1]
local now         = tonumber(ARGV[1])
local window_start = now - tonumber(ARGV[2])
local limit       = tonumber(ARGV[3])
local ttl         = tonumber(ARGV[4])
local member      = ARGV[5]
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
local count = redis.call('ZCARD', key)
if count >= limit then
  return 0
end
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, ttl)
return 1
"""


def _get_redis() -> "aioredis.Redis | None":
    global _redis_client, _redis_init_done
    if _redis_init_done:
        return _redis_client
    _redis_init_done = True
    try:
        from core.config import get_settings
        url = get_settings().redis_url
        if not url:
            return None
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=1)
        logger.info("Rate limiter: using Redis backend ({})", url)
    except Exception as exc:
        logger.warning("Rate limiter: Redis init failed, falling back to in-memory ({})", exc)
        _redis_client = None
    return _redis_client


async def _enforce_redis(
    redis: "aioredis.Redis",
    bucket_key: str,
    limit: int,
    window_seconds: int,
) -> None:
    now = time.time()
    member = f"{now:.6f}:{random.getrandbits(32)}"
    try:
        allowed = await redis.eval(
            _LUA_SLIDING_WINDOW,
            1,
            bucket_key,
            now,
            window_seconds,
            limit,
            window_seconds + 1,
            member,
        )
    except Exception as exc:
        logger.warning("Rate limiter Redis error, falling back to allow: {}", exc)
        return  # Fail open — don't block requests if Redis is down.
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(window_seconds)},
        )


# ---------------------------------------------------------------------------
# In-memory backend (fallback)
# ---------------------------------------------------------------------------
_RATE_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)
_RATE_LOCK = Lock()


def _enforce_memory(bucket_key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def enforce_rate_limit(
    request: Request,
    scope: str,
    limit: int,
    window_seconds: int,
) -> None:
    if limit <= 0 or window_seconds <= 0:
        return

    bucket_key = f"rl:{scope}:{_client_ip(request)}"
    redis = _get_redis()
    if redis is not None:
        await _enforce_redis(redis, bucket_key, limit, window_seconds)
    else:
        _enforce_memory(bucket_key, limit, window_seconds)
