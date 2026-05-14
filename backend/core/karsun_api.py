"""Karsun JS-LPRO1 camera API client.

All functions are stubs returning False with a logger.warning until the
official Karsun HTTP API specification is received from the vendor.

Vendor documentation required for:
  - Whitelist add/remove endpoint request/response format and auth mechanism
  - Relay command endpoint format
  - HTTP event push (webhook) payload field names

Do NOT raise exceptions from any function here — camera unavailability must
never crash the server.  The DB operation is always the source of truth.
"""
from __future__ import annotations

from loguru import logger

from core.config import get_settings
from models.vehicle import VehicleStatus


_STUB_WARNING = (
    "Karsun API stub called — vendor HTTP API documentation not yet received. "
    "Camera was NOT updated. Set KARSUN_IP and implement real calls once spec is available."
)


async def sync_vehicle_to_camera(plate: str, status: VehicleStatus) -> bool:
    """Add plate to camera whitelist (allowed) or remove it (denied/blacklist/blocked).

    Returns True on success, False on any failure.
    """
    settings = get_settings()
    if not settings.karsun_ip:
        logger.warning(f"{_STUB_WARNING} | operation=sync plate={plate} status={status}")
        return False

    # TODO: implement after vendor API spec received.
    # Pseudocode:
    #   if status == VehicleStatus.ALLOWED:
    #       POST {karsun_ip}{karsun_whitelist_add_path} with plate payload
    #   else:
    #       await remove_vehicle_from_camera(plate)
    logger.warning(f"{_STUB_WARNING} | operation=sync plate={plate} status={status}")
    return False


async def remove_vehicle_from_camera(plate: str) -> bool:
    """Remove plate from camera internal whitelist/blacklist memory.

    Returns True on success, False on any failure.
    """
    settings = get_settings()
    if not settings.karsun_ip:
        logger.warning(f"{_STUB_WARNING} | operation=remove plate={plate}")
        return False

    # TODO: implement after vendor API spec received.
    # Pseudocode:
    #   POST {karsun_ip}{karsun_whitelist_remove_path} with plate payload
    logger.warning(f"{_STUB_WARNING} | operation=remove plate={plate}")
    return False


async def trigger_relay() -> bool:
    """Send relay close command to camera for manual gate open.

    Returns True on success, False on any failure.
    """
    settings = get_settings()
    if not settings.karsun_ip:
        logger.warning(f"{_STUB_WARNING} | operation=trigger_relay")
        return False

    # TODO: implement after vendor API spec received.
    # Pseudocode:
    #   POST {karsun_ip}{karsun_relay_path}
    logger.warning(f"{_STUB_WARNING} | operation=trigger_relay")
    return False
