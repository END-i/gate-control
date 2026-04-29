import httpx
from loguru import logger

from core.config import get_settings

async def trigger_relay() -> bool:
    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                settings.relay_ip,
                auth=(settings.relay_username, settings.relay_password),
            )
            if response.status_code // 100 != 2:
                logger.warning('Relay trigger failed with status {}', response.status_code)
                return False
            return True
    except httpx.TimeoutException:
        logger.warning('Relay trigger timeout')
        return False
    except httpx.HTTPError as exc:
        logger.warning('Relay trigger HTTP error: {}', exc)
        return False
