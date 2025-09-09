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
        self.audio_outputs: Dict[str, str] = {}  # NEW: Store available audio outputs
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
            # Discover EQ presets
            if eq_list := await self.get_eq_list():
                self.eq_presets = eq_list
                _LOG.info("Discovered %d EQ presets", len(self.eq_presets))
                
            # Discover user presets    
            if preset_info := await self.get_preset_info():
                self.presets = preset_info.get('preset_list', [])
                _LOG.info("Discovered %d user presets", len(self.presets))
                
            # Discover audio outputs (NEW)
            await self._discover_audio_outputs()
        
        # Set up default input sources (these are standard across WiiM devices)
        self.sources = {
            'wifi': 'WiFi', 'bluetooth': 'Bluetooth', 'line-in': 'Line In',
            'optical': 'Optical', 'HDMI': 'HDMI', 'phono': 'Phono', 'udisk': 'USB'
        }
        _LOG.info("Capability discovery completed")

    async def _discover_audio_outputs(self):
        """Discover available audio output modes."""
        try:
            resp = await self.send_command("getNewAudioOutputHardwareMode")
            if not resp:
                _LOG.warning("Could not query audio output capabilities")
                return
                
            try:
                output_info = json.loads(resp)
                _LOG.info("Audio output info: %s", output_info)
                
                # Build available outputs based on device response and API documentation
                self.audio_outputs = {}
                
                # Standard audio output modes from API documentation
                output_modes = {
                    '1': 'SPDIF',
                    '2': 'AUX/Line Out', 
                    '3': 'COAX'
                }
                
                # Current hardware mode from your device response
                current_hardware = output_info.get('hardware', '0')
                _LOG.info("Current hardware output mode: %s (%s)", current_hardware, 
                         output_modes.get(current_hardware, 'Unknown'))
                
                # Add all standard modes (most WiiM devices support all three)
                for mode_id, mode_name in output_modes.items():
                    cmd_name = f"output_{mode_name.lower().replace('/', '_').replace(' ', '_')}"
                    self.audio_outputs[cmd_name] = mode_name
                
                # Check for additional output capabilities
                if output_info.get('source', '0') == '1':
                    self.audio_outputs['output_bt_source'] = 'BT Source Output'
                    _LOG.info("BT Source Output capability detected")
                    
                if output_info.get('audiocast', '0') == '1':
                    self.audio_outputs['output_audiocast'] = 'Audio Cast Output'
                    _LOG.info("Audio Cast Output capability detected")
                
                _LOG.info("Discovered audio outputs: %s", list(self.audio_outputs.keys()))
                
            except json.JSONDecodeError:
                _LOG.warning("Could not parse audio output info JSON: %s", resp)
                # Fallback to standard outputs
                self._set_fallback_audio_outputs()
                
        except Exception as e:
            _LOG.error("Error discovering audio outputs: %s", e)
            # Fallback to standard outputs for most WiiM devices
            self._set_fallback_audio_outputs()

    def _set_fallback_audio_outputs(self):
        """Set fallback audio outputs for when discovery fails."""
        self.audio_outputs = {
            'output_spdif': 'SPDIF',
            'output_aux_line_out': 'AUX/Line Out',
            'output_coax': 'COAX'
        }
        _LOG.info("Using fallback audio outputs: %s", list(self.audio_outputs.keys()))

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

    async def get_audio_output_info(self) -> Optional[Dict[str, Any]]:
        """Get current audio output configuration."""
        resp = await self.send_command("getNewAudioOutputHardwareMode")
        try:
            return json.loads(resp) if resp else None
        except json.JSONDecodeError:
            return None

    async def set_audio_output_mode(self, mode: int) -> bool:
        """Set audio output hardware mode."""
        resp = await self.send_command(f"setAudioOutputHardwareMode:{mode}")
        return resp == "OK"

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