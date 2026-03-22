"""
WiiM Device HTTP API Client.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import time
from typing import Any

import aiohttp

from uc_intg_wiim.const import (
    UNKNOWN_METADATA_VALUES,
    WIIM_API_TIMEOUT,
    WIIM_THROTTLE_DELAY,
)

_LOG = logging.getLogger(__name__)


class WiiMClient:
    """HTTP API client for WiiM audio devices."""

    def __init__(self, host: str) -> None:
        self._host = host
        self._session: aiohttp.ClientSession | None = None
        self._last_command_time: float = 0

    @property
    def host(self) -> str:
        return self._host

    async def connect(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=10),
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def send_command(self, command: str) -> str | None:
        """Send an HTTP GET command to the WiiM device API."""
        await self.connect()
        elapsed = time.time() - self._last_command_time
        if elapsed < WIIM_THROTTLE_DELAY:
            await asyncio.sleep(WIIM_THROTTLE_DELAY - elapsed)
        self._last_command_time = time.time()

        url = f"http://{self._host}/httpapi.asp?command={command}"
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=WIIM_API_TIMEOUT)
            ) as resp:
                if resp.status == 200:
                    return await resp.text()
                _LOG.error("API request failed with status %d: %s", resp.status, command)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOG.debug("API request error for '%s': %s", command, err)
        except Exception as err:
            _LOG.error("Unexpected API error for '%s': %s", command, err)
        return None

    async def _send_json_command(self, command: str) -> dict[str, Any] | None:
        """Send command and parse JSON response."""
        resp = await self.send_command(command)
        if not resp:
            return None
        try:
            return json.loads(resp)
        except json.JSONDecodeError:
            _LOG.debug("Non-JSON response for '%s': %s", command, resp[:100])
            return None

    async def test_connection(self) -> bool:
        return await self.get_device_info() is not None

    # ── Device Info ──────────────────────────────────────────────────

    async def get_device_info(self) -> dict[str, Any] | None:
        return await self._send_json_command("getStatusEx")

    async def get_player_status(self) -> dict[str, Any] | None:
        return await self._send_json_command("getPlayerStatus")

    async def get_track_metadata(self) -> dict[str, Any] | None:
        data = await self._send_json_command("getMetaInfo")
        if data and "metaData" in data:
            return data["metaData"]
        return data

    async def get_eq_list(self) -> list[str] | None:
        resp = await self.send_command("EQGetList")
        if not resp:
            return None
        try:
            result = json.loads(resp)
            return result if isinstance(result, list) else None
        except json.JSONDecodeError:
            return None

    async def get_preset_info(self) -> dict[str, Any] | None:
        return await self._send_json_command("getPresetInfo")

    async def get_audio_output_info(self) -> dict[str, Any] | None:
        return await self._send_json_command("getNewAudioOutputHardwareMode")

    # ── Playback Commands ────────────────────────────────────────────

    async def resume(self) -> bool:
        return await self.send_command("setPlayerCmd:resume") is not None

    async def pause(self) -> bool:
        return await self.send_command("setPlayerCmd:pause") is not None

    async def toggle_playback(self) -> bool:
        return await self.send_command("setPlayerCmd:onepause") is not None

    async def stop(self) -> bool:
        return await self.send_command("setPlayerCmd:stop") is not None

    async def next_track(self) -> bool:
        return await self.send_command("setPlayerCmd:next") is not None

    async def previous_track(self) -> bool:
        return await self.send_command("setPlayerCmd:prev") is not None

    # ── Volume Commands ──────────────────────────────────────────────

    async def set_volume(self, volume: int) -> bool:
        volume = max(0, min(100, volume))
        return await self.send_command(f"setPlayerCmd:vol:{volume}") is not None

    async def set_mute(self, muted: bool) -> bool:
        return await self.send_command(f"setPlayerCmd:mute:{1 if muted else 0}") is not None

    # ── Source / Input Commands ──────────────────────────────────────

    async def switch_source(self, source: str) -> bool:
        return await self.send_command(f"setPlayerCmd:switchmode:{source}") is not None

    async def activate_preset(self, preset_number: int) -> bool:
        return await self.send_command(f"MCUKeyShortClick:{preset_number}") is not None

    # ── Audio Output Commands ────────────────────────────────────────

    async def set_audio_output(self, mode: int) -> bool:
        resp = await self.send_command(f"setAudioOutputHardwareMode:{mode}")
        return resp == "OK"

    # ── Equalizer Commands ───────────────────────────────────────────

    async def set_eq_preset(self, preset_name: str) -> bool:
        return await self.send_command(f"EQLoad:{preset_name}") is not None

    async def set_eq_enabled(self, enabled: bool) -> bool:
        cmd = "EQOn" if enabled else "EQOff"
        return await self.send_command(cmd) is not None

    # ── Device Control Commands ──────────────────────────────────────

    async def set_display(self, enabled: bool) -> bool:
        val = 0 if enabled else 1
        cmd = f'setLightOperationBrightConfig:{{"disable":{val}}}'
        return await self.send_command(cmd) is not None

    async def reboot(self) -> bool:
        return await self.send_command("reboot") is not None

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def clean_metadata_value(value: str | None) -> str | None:
        """Return None if value is a WiiM placeholder or empty."""
        if not value or value.strip().lower() in UNKNOWN_METADATA_VALUES:
            return None
        return value.strip()
