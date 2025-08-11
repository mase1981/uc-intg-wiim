"""
WiiM Integration Driver for Unfolded Circle Remote Two.

:copyright: (c) 2025 by Meir Miyara.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import logging
import os
from typing import List, Optional

import ucapi
from ucapi import DeviceStates, Events, IntegrationSetupError, SetupComplete, SetupError

from uc_intg_wiim.client import WiiMClient
from uc_intg_wiim.config import Config
from uc_intg_wiim.media_player import WiiMMediaPlayer
from uc_intg_wiim.remote import WiiMRemote

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOG = logging.getLogger(__name__)

api: Optional[ucapi.IntegrationAPI] = None
config: Optional[Config] = None
client: Optional[WiiMClient] = None
update_task: Optional[asyncio.Task] = None
media_player_entity: Optional[WiiMMediaPlayer] = None
remote_entity: Optional[WiiMRemote] = None

async def setup_entities_from_device():
    """Create and configure entities based on discovered device capabilities."""
    global client, api, config, update_task, media_player_entity, remote_entity
    
    if not config or not config.is_configured():
        _LOG.error("Configuration not found or invalid")
        await api.set_device_state(DeviceStates.ERROR)
        return

    _LOG.info("Connecting to WiiM device...")
    await api.set_device_state(DeviceStates.CONNECTING)
    
    try:
        host = config.get_host()
        client = WiiMClient(host)
        
        if not await client.test_connection():
            _LOG.error("Failed to connect to WiiM device at %s", host)
            await api.set_device_state(DeviceStates.ERROR)
            return

        device_info = await client.get_device_info()
        if not device_info:
            _LOG.error("Failed to get device information")
            await api.set_device_state(DeviceStates.ERROR)
            return
            
        device_name = device_info.get('DeviceName', 'WiiM Device')
        device_id = device_info.get('uuid', 'WIIM_DEVICE').replace("-", "")
        
        _LOG.info("Connected to WiiM device: %s (ID: %s)", device_name, device_id)
        
        await client.discover_capabilities()
        
        # Create entities with correct constructor signature
        media_player_entity = WiiMMediaPlayer(device_id, device_name)
        remote_entity = WiiMRemote(device_id, device_name)
        
        # Set client for both entities
        media_player_entity.set_client(client)
        remote_entity.set_client(client)
        
        media_player_entity._integration_api = api
        remote_entity._integration_api = api
        
        api.available_entities.add(media_player_entity)
        api.available_entities.add(remote_entity)
        api.configured_entities.add(media_player_entity)
        api.configured_entities.add(remote_entity)
        
        await remote_entity.initialize_capabilities()
        await media_player_entity.initialize_and_set_state()
        
        if update_task:
            update_task.cancel()
        update_task = asyncio.create_task(periodic_update())
        
        await api.set_device_state(DeviceStates.CONNECTED)
        _LOG.info("WiiM integration setup completed successfully")
        
    except Exception as e:
        _LOG.error("Connection failed during setup: %s", e, exc_info=True)
        await api.set_device_state(DeviceStates.ERROR)

async def setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    """Handle driver setup requests."""
    global config
    
    if isinstance(msg, ucapi.DriverSetupRequest):
        host = msg.setup_data.get("host")
        if not host:
            _LOG.error("No host provided in setup data")
            return SetupError(IntegrationSetupError.OTHER)
            
        _LOG.info("Testing connection to WiiM device at %s", host)
        
        try:
            test_client = WiiMClient(host)
            if not await test_client.test_connection():
                _LOG.error("Connection test failed for host: %s", host)
                await test_client.close()
                return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
            
            await test_client.close()
            
            config.set("host", host)
            config.save()
            
            asyncio.create_task(setup_entities_from_device())
            return SetupComplete()
            
        except Exception as e:
            _LOG.error("Setup error: %s", e)
            return SetupError(IntegrationSetupError.OTHER)
    
    return SetupComplete()

async def periodic_update():
    """Periodically update entity states."""
    global media_player_entity, remote_entity
    
    _LOG.info("Starting periodic update task")
    
    if media_player_entity:
        await media_player_entity.update_attributes()
    if remote_entity:
        await remote_entity.update_attributes()
    
    while True:
        try:
            await asyncio.sleep(5.0)
            
            if (api.device_state == DeviceStates.CONNECTED and 
                media_player_entity and remote_entity and client):
                
                await media_player_entity.update_attributes()
                await remote_entity.update_attributes()
                
        except asyncio.CancelledError:
            _LOG.info("Periodic update task cancelled")
            break
        except Exception as e:
            _LOG.error("Error in periodic update: %s", e)

async def on_subscribe_entities(entity_ids: List[str]):
    """Handle entity subscription events."""
    global media_player_entity, remote_entity
    
    _LOG.info("Entities subscribed: %s", entity_ids)
    
    if media_player_entity and media_player_entity.id in entity_ids:
        _LOG.info("Media Player subscribed, forcing update")
        await media_player_entity.update_attributes()
        
    if remote_entity and remote_entity.id in entity_ids:
        _LOG.info("Remote subscribed, forcing update")
        await remote_entity.update_attributes()

async def on_unsubscribe_entities(entity_ids: List[str]):
    """Handle entity unsubscription events."""
    _LOG.info("Entities unsubscribed: %s", entity_ids)

async def on_connect():
    """Handle connection events."""
    _LOG.info("Remote Two connected")

async def on_disconnect():
    """Handle disconnection events."""
    _LOG.info("Remote Two disconnected")

async def main():
    """Main driver entry point."""
    global api, config
    
    _LOG.info("Starting WiiM Integration Driver")
    
    try:
        loop = asyncio.get_running_loop()
        config = Config()
        config.load()
        
        driver_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
        api = ucapi.IntegrationAPI(loop)
        await api.init(os.path.abspath(driver_path), setup_handler)

        api.add_listener(Events.SUBSCRIBE_ENTITIES, on_subscribe_entities)
        api.add_listener(Events.UNSUBSCRIBE_ENTITIES, on_unsubscribe_entities)
        api.add_listener(Events.CONNECT, on_connect)
        api.add_listener(Events.DISCONNECT, on_disconnect)
        
        if config.is_configured():
            _LOG.info("Device already configured, starting connection...")
            asyncio.create_task(setup_entities_from_device())
        else:
            _LOG.info("Device not configured, waiting for setup...")
            await api.set_device_state(DeviceStates.DISCONNECTED)

        await asyncio.Future()
        
    except Exception as e:
        _LOG.error("Fatal error in main: %s", e, exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        _LOG.info("Driver stopped by user")
    except Exception as e:
        _LOG.error("Driver crashed: %s", e, exc_info=True)