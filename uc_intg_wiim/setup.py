"""
Setup handler for the WiiM integration.
This file is currently not used directly as the setup logic
is contained within driver.py, but it is corrected here for
consistency and future use.
"""
import asyncio
import logging
from typing import Any, Tuple

import aiohttp
import ucapi.api_definitions as uc
from ucapi import IntegrationSetupError

from uc_intg_wiim.client import WiiMClient

_LOGGER = logging.getLogger(__name__)

async def handle_setup(
    setup_request: uc.DriverSetupRequest
) -> Tuple[WiiMClient, dict[str, Any], aiohttp.ClientSession] | uc.SetupError:
    """
    Handle the driver setup process.

    Tests the connection and returns a client instance on success.
    """
    host = setup_request.setup_data.get("host")
    if not host:
        return uc.SetupError(IntegrationSetupError.OTHER)

    _LOGGER.info("Handling setup for host: %s", host)
    
    session = aiohttp.ClientSession()
    client = WiiMClient(host, session)
    
    try:
        device_info = await client.get_device_info()
        if not device_info or not device_info.get("uuid"):
            raise ConnectionError("Invalid response from device, cannot get UUID.")
        
        _LOGGER.info("Successfully connected to WiiM device: %s", device_info.get("DeviceName", host))
        return client, device_info, session

    # --- MODIFICATION START ---
    except (aiohttp.ClientError, ConnectionError, asyncio.TimeoutError) as e:
        _LOGGER.error(f"Setup failed due to connection issue: {e}")
        await session.close()
        return uc.SetupError(IntegrationSetupError.CONNECTION_REFUSED)
    except Exception as e:
        _LOGGER.error(f"An unexpected error occurred during setup: {e}")
        await session.close()
        return uc.SetupError(IntegrationSetupError.OTHER)
    # --- MODIFICATION END ---