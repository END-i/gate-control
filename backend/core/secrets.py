"""Optional Vault / AWS SSM secrets adapter.

When ``VAULT_ADDR`` and ``VAULT_TOKEN`` are set, :func:`prefetch_secrets`
reads the KV-v2 secret at ``VAULT_SECRET_PATH`` (default
``secret/data/anpr``) and injects each key as an environment variable.
pydantic-settings then picks them up normally via its env-var source.

If Vault is unreachable or not configured the function is a no-op —
normal env-var / ``.env`` file loading proceeds unchanged.

Usage in ``main.py`` (before ``get_settings()`` is called)::

    from core.secrets import prefetch_secrets
    prefetch_secrets()
    settings = get_settings()
"""
from __future__ import annotations

import os
from typing import Any

from loguru import logger


def prefetch_secrets() -> None:
    """Fetch secrets from Vault and inject into :data:`os.environ`.

    Called once at module import time in ``main.py``, before
    ``get_settings()`` so that pydantic-settings sees the Vault-sourced
    values as ordinary env vars.  Any key that is **already** present in
    the environment is left unchanged (env var wins over Vault).

    No-op when ``VAULT_ADDR`` is not set.
    """
    vault_addr = os.getenv("VAULT_ADDR", "").rstrip("/")
    vault_token = os.getenv("VAULT_TOKEN", "")
    if not vault_addr or not vault_token:
        return

    secret_path = os.getenv("VAULT_SECRET_PATH", "secret/data/anpr").lstrip("/")
    url = f"{vault_addr}/v1/{secret_path}"

    try:
        import httpx  # already in requirements.txt

        resp = httpx.get(
            url,
            headers={"X-Vault-Token": vault_token},
            timeout=5.0,
        )
        resp.raise_for_status()
        payload: dict[str, Any] = resp.json()
        # KV-v2 wraps secrets under {"data": {"data": {...}}}
        # KV-v1 puts them directly under {"data": {...}}
        data = payload.get("data", {})
        secrets: dict[str, str] = data.get("data", data)
        injected = 0
        for key, value in secrets.items():
            if key not in os.environ:
                os.environ[key] = str(value)
                injected += 1
        logger.info(
            "Vault: prefetched {}/{} secret(s) from {}",
            injected,
            len(secrets),
            url,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Vault secret prefetch failed ({}); falling back to env vars / .env",
            exc,
        )
