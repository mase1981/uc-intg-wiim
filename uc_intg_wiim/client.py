"""
WiiM Device Client Implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp

_LOG = logging.getLogger(__name__)

class WiiMClient:
    """Client for interacting with the WiiM HTTP API."""

    def __init__(self, host: str):
        """Initialize WiiM client."""
        self.host = host
        self.session: Optional[aiohttp.ClientSession] = None
        self.sources: Dict[str, str] = {}
        self.eq_presets: List[str] = []
        self.presets: List[Dict[str, Any]] = []
        self._last_command_time = 0
        self._throttle_delay = 0.2

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure HTTP session is available."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=10)
            )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def send_command(self, command: str) -> Optional[str]:
        """Send HTTP command to WiiM device."""
        await self._ensure_session()
        
        time_since_last = time.time() - self._last_command_time
        if time_since_last < self._throttle_delay:
            await asyncio.sleep(self._throttle_delay - time_since_last)
        
        self._last_command_time = time.time()
        url = f"https://{self.host}/httpapi.asp?command={command}"
        _LOG.debug("Request: %s", url)
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.text()
                _LOG.error("API request failed: %s", response.status)
        except Exception as e:
            _LOG.error("API request error: %s", e)
        return None

    async def test_connection(self) -> bool:
        """Test connection to WiiM device."""
        return bool(await self.get_device_info())

    async def discover_capabilities(self):
        """Discover and cache device capabilities."""
        _LOG.info("Discovering device capabilities...")
        
        if await self.get_device_info():
            if eq_list := await self.get_eq_list():
                self.eq_presets = eq_list
                _LOG.info("Discovered %d EQ presets", len(self.eq_presets))
                
            if preset_info := await self.get_preset_info():
                self.presets = preset_info.get('preset_list', [])
                _LOG.info("Discovered %d user presets", len(self.presets))
        
        self.sources = {
            'wifi': 'WiFi', 'bluetooth': 'Bluetooth', 'line-in': 'Line In',
            'optical': 'Optical', 'HDMI': 'HDMI', 'phono': 'Phono', 'udisk': 'USB'
        }
        _LOG.info("Capability discovery completed")

    async def get_device_info(self) -> Optional[Dict[str, Any]]:
        """Get device information."""
        resp = await self.send_command("getStatusEx")
        try:
            return json.loads(resp) if resp else None
        except json.JSONDecodeError:
            return None

    async def get_player_status(self) -> Optional[Dict[str, Any]]:
        """Get current player status."""
        resp = await self.send_command("getPlayerStatus")
        try:
            return json.loads(resp) if resp else None
        except json.JSONDecodeError:
            return None

    async def get_track_metadata(self) -> Optional[Dict[str, Any]]:
        """Get current track metadata."""
        resp = await self.send_command("getMetaInfo")
        try:
            return json.loads(resp).get('metaData') if resp else None
        except json.JSONDecodeError:
            return None

    async def get_eq_list(self) -> Optional[List[str]]:
        """Get available EQ presets."""
        resp = await self.send_command("EQGetList")
        try:
            return json.loads(resp) if resp else None
        except json.JSONDecodeError:
            return None

    async def get_preset_info(self) -> Optional[Dict[str, Any]]:
        """Get user preset information."""
        resp = await self.send_command("getPresetInfo")
        try:
            return json.loads(resp) if resp else None
        except json.JSONDecodeError:
            return None

    async def resume_playback(self):
        """Resume playback."""
        await self.send_command("setPlayerCmd:resume")

    async def pause_playback(self):
        """Pause playback."""
        await self.send_command("setPlayerCmd:pause")

    async def toggle_playback(self):
        """Toggle play/pause."""
        await self.send_command("setPlayerCmd:onepause")

    async def stop_playback(self):
        """Stop playback."""
        await self.send_command("setPlayerCmd:stop")

    async def next_track(self):
        """Skip to next track."""
        await self.send_command("setPlayerCmd:next")

    async def previous_track(self):
        """Skip to previous track."""
        await self.send_command("setPlayerCmd:prev")
    
    async def set_volume(self, volume: int):
        """Set volume level (0-100)."""
        volume = max(0, min(100, volume))
        await self.send_command(f"setPlayerCmd:vol:{volume}")
        
    async def volume_up(self):
        """Increase volume by 5."""
        if status := await self.get_player_status():
            current_vol = int(status.get('vol', 50))
            await self.set_volume(min(100, current_vol + 5))
            
    async def volume_down(self):
        """Decrease volume by 5."""
        if status := await self.get_player_status():
            current_vol = int(status.get('vol', 50))
            await self.set_volume(max(0, current_vol - 5))

    async def set_mute(self, muted: bool):
        """Set mute state."""
        await self.send_command(f"setPlayerCmd:mute:{1 if muted else 0}")
        
    async def toggle_mute(self):
        """Toggle mute state."""
        if status := await self.get_player_status():
            current_mute = status.get('mute') == '1'
            await self.set_mute(not current_mute)