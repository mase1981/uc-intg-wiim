"""
WiiM device implementation using PollingDevice.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from urllib.parse import unquote

from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_wiim.client import WiiMClient
from uc_intg_wiim.config import WiiMDeviceConfig
from uc_intg_wiim.const import (
    AUDIO_OUTPUT_MODES,
    LOOP_MODE_MAP,
    PHYSICAL_SOURCES,
    PLAYBACK_MODE_MAP,
    VOLUME_STEP,
    WIIM_POLL_INTERVAL,
)

_LOG = logging.getLogger(__name__)


class WiiMDevice(PollingDevice):
    """WiiM audio device managed via HTTP polling."""

    def __init__(self, device_config: WiiMDeviceConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=WIIM_POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: WiiMClient | None = None

        self._state: str = "UNAVAILABLE"
        self._volume: int = 0
        self._muted: bool = False
        self._repeat: str = "OFF"
        self._shuffle: bool = False
        self._source: str = ""
        self._source_list: list[str] = []

        self._media_title: str | None = None
        self._media_artist: str | None = None
        self._media_album: str | None = None
        self._media_image_url: str | None = None
        self._media_duration: int = 0
        self._media_position: int = 0
        self._media_type: str = "MUSIC"

        self._device_name: str = device_config.name
        self._firmware: str | None = None
        self._hardware: str | None = None
        self._wifi_ssid: str | None = None
        self._ip_address: str | None = None
        self._current_mode: str = "0"

        self._eq_presets: list[str] = list(device_config.eq_presets)
        self._current_eq: str | None = None
        self._audio_outputs: dict[str, str] = dict(device_config.audio_outputs)
        self._current_audio_output: str | None = None
        self._presets: list[dict] = list(device_config.presets)
        self._music_services: list[str] = list(device_config.music_services)

        self._build_source_list()

    # ── PollingDevice interface ──────────────────────────────────────

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_name

    @property
    def address(self) -> str:
        return self._device_config.host

    @property
    def log_id(self) -> str:
        return f"{self.name} ({self.address})"

    async def establish_connection(self) -> WiiMClient:
        self._client = WiiMClient(self._device_config.host)
        await self._client.connect()

        if not await self._client.test_connection():
            await self._client.close()
            self._client = None
            raise ConnectionError(f"Cannot reach WiiM device at {self._device_config.host}")

        await self._discover_capabilities()
        await self._fetch_device_info()
        try:
            await self._update_player_state()
        except ConnectionError:
            _LOG.warning("[%s] Initial player state query failed, continuing with defaults", self.log_id)

        self._state = "ON"
        _LOG.info("[%s] Connected successfully", self.log_id)
        return self._client

    async def poll_device(self) -> None:
        if not self._client:
            return
        try:
            await self._update_player_state()
            self.push_update()
        except Exception as err:
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != "UNAVAILABLE":
                self._state = "UNAVAILABLE"
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        self._state = "UNAVAILABLE"
        await super().disconnect()

    # ── State Properties ─────────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._state

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def repeat_mode(self) -> str:
        return self._repeat

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    @property
    def source(self) -> str:
        return self._source

    @property
    def source_list(self) -> list[str]:
        return self._source_list

    @property
    def media_title(self) -> str | None:
        return self._media_title

    @property
    def media_artist(self) -> str | None:
        return self._media_artist

    @property
    def media_album(self) -> str | None:
        return self._media_album

    @property
    def media_image_url(self) -> str | None:
        return self._media_image_url

    @property
    def media_duration(self) -> int:
        return self._media_duration

    @property
    def media_position(self) -> int:
        return self._media_position

    @property
    def media_type(self) -> str:
        return self._media_type

    @property
    def firmware(self) -> str | None:
        return self._firmware

    @property
    def hardware(self) -> str | None:
        return self._hardware

    @property
    def wifi_ssid(self) -> str | None:
        return self._wifi_ssid

    @property
    def ip_address(self) -> str | None:
        return self._ip_address

    @property
    def eq_presets(self) -> list[str]:
        return self._eq_presets

    @property
    def current_eq(self) -> str | None:
        return self._current_eq

    @property
    def audio_outputs(self) -> dict[str, str]:
        return self._audio_outputs

    @property
    def current_audio_output(self) -> str | None:
        return self._current_audio_output

    @property
    def presets(self) -> list[dict]:
        return self._presets

    @property
    def music_services(self) -> list[str]:
        return self._music_services

    # ── Playback Commands ────────────────────────────────────────────

    async def cmd_play_pause(self) -> bool:
        if not self._client:
            return False
        return await self._client.toggle_playback()

    async def cmd_stop(self) -> bool:
        if not self._client:
            return False
        result = await self._client.stop()
        if result:
            self._state = "ON"
            self._clear_media()
            self.push_update()
        return result

    async def cmd_next(self) -> bool:
        if not self._client:
            return False
        return await self._client.next_track()

    async def cmd_previous(self) -> bool:
        if not self._client:
            return False
        return await self._client.previous_track()

    async def cmd_set_volume(self, volume: int) -> bool:
        if not self._client:
            return False
        result = await self._client.set_volume(volume)
        if result:
            self._volume = max(0, min(100, volume))
            self.push_update()
        return result

    async def cmd_volume_up(self) -> bool:
        return await self.cmd_set_volume(min(100, self._volume + VOLUME_STEP))

    async def cmd_volume_down(self) -> bool:
        return await self.cmd_set_volume(max(0, self._volume - VOLUME_STEP))

    async def cmd_mute(self, muted: bool) -> bool:
        if not self._client:
            return False
        result = await self._client.set_mute(muted)
        if result:
            self._muted = muted
            self.push_update()
        return result

    async def cmd_mute_toggle(self) -> bool:
        return await self.cmd_mute(not self._muted)

    async def cmd_select_source(self, source_name: str) -> bool:
        if not self._client:
            return False

        source_key = self._resolve_source_key(source_name)
        if not source_key:
            _LOG.warning("[%s] Unknown source: %s", self.log_id, source_name)
            return False

        if source_key in PHYSICAL_SOURCES:
            result = await self._client.switch_source(source_key)
        else:
            result = await self._activate_service_preset(source_name)

        if result:
            self._source = source_name
            self._clear_media()
            self.push_update()
        return result

    # ── EQ Commands ──────────────────────────────────────────────────

    async def cmd_set_eq(self, preset_name: str) -> bool:
        if not self._client:
            return False
        if preset_name == "Off":
            result = await self._client.set_eq_enabled(False)
        else:
            result = await self._client.set_eq_preset(preset_name)
            if result:
                await self._client.set_eq_enabled(True)
        if result:
            self._current_eq = preset_name
            self.push_update()
        return result

    # ── Audio Output Commands ────────────────────────────────────────

    async def cmd_set_audio_output(self, output_name: str) -> bool:
        if not self._client:
            return False
        mode_id = self._get_output_mode_id(output_name)
        if mode_id is None:
            _LOG.warning("[%s] Unknown audio output: %s", self.log_id, output_name)
            return False
        result = await self._client.set_audio_output(int(mode_id))
        if result:
            self._current_audio_output = output_name
            self.push_update()
        return result

    # ── Device Control ───────────────────────────────────────────────

    async def cmd_display_on(self) -> bool:
        if not self._client:
            return False
        return await self._client.set_display(True)

    async def cmd_display_off(self) -> bool:
        if not self._client:
            return False
        return await self._client.set_display(False)

    async def cmd_reboot(self) -> bool:
        if not self._client:
            return False
        return await self._client.reboot()

    async def cmd_activate_preset(self, preset_number: int) -> bool:
        if not self._client:
            return False
        return await self._client.activate_preset(preset_number)

    # ── Internal Methods ─────────────────────────────────────────────

    async def _discover_capabilities(self) -> None:
        if not self._client:
            return

        eq_list = await self._client.get_eq_list()
        if eq_list:
            self._eq_presets = eq_list
            _LOG.info("[%s] Discovered %d EQ presets", self.log_id, len(eq_list))

        preset_info = await self._client.get_preset_info()
        if preset_info:
            self._presets = preset_info.get("preset_list", [])
            self._music_services = self._extract_music_services(self._presets)
            _LOG.info(
                "[%s] Discovered %d presets, %d music services",
                self.log_id,
                len(self._presets),
                len(self._music_services),
            )

        await self._discover_audio_outputs()
        self._build_source_list()

    async def _discover_audio_outputs(self) -> None:
        if not self._client:
            return
        output_info = await self._client.get_audio_output_info()
        if output_info:
            self._audio_outputs = {}
            for mode_id, mode_name in AUDIO_OUTPUT_MODES.items():
                self._audio_outputs[mode_id] = mode_name
            if output_info.get("source", "0") == "1":
                self._audio_outputs["bt_source"] = "BT Source"
            if output_info.get("audiocast", "0") == "1":
                self._audio_outputs["audiocast"] = "Audio Cast"
            current = output_info.get("hardware", "0")
            self._current_audio_output = AUDIO_OUTPUT_MODES.get(current)
            _LOG.info("[%s] Audio outputs: %s", self.log_id, list(self._audio_outputs.values()))
        else:
            self._audio_outputs = dict(AUDIO_OUTPUT_MODES)

    async def _fetch_device_info(self) -> None:
        if not self._client:
            return
        info = await self._client.get_device_info()
        if not info:
            return
        self._device_name = info.get("DeviceName", self._device_config.name)
        self._firmware = info.get("firmware", None)
        self._hardware = info.get("hardware", None)
        ssid = info.get("ssid", None)
        self._wifi_ssid = unquote(ssid) if ssid else None
        eth2 = info.get("eth2", "")
        apcli0 = info.get("apcli0", "")
        if eth2 and eth2 != "0.0.0.0":
            self._ip_address = eth2
        elif apcli0 and apcli0 != "0.0.0.0":
            self._ip_address = apcli0
        else:
            self._ip_address = self._device_config.host

    async def _update_player_state(self) -> None:
        if not self._client:
            return
        status = await self._client.get_player_status()
        if not status:
            raise ConnectionError("Failed to get player status")

        self._volume = int(status.get("vol", self._volume))
        self._muted = status.get("mute") == "1"

        loop_val = status.get("loop", "0")
        self._repeat = LOOP_MODE_MAP.get(loop_val, "OFF")
        self._shuffle = loop_val in ("2", "3")

        play_status = status.get("status", "stop")
        old_mode = self._current_mode
        self._current_mode = status.get("mode", "0")

        if old_mode != self._current_mode:
            self._clear_media()

        if play_status == "play":
            self._state = "PLAYING"
        elif play_status == "pause":
            self._state = "PAUSED"
        else:
            self._state = "ON"

        self._source = PLAYBACK_MODE_MAP.get(self._current_mode, "Unknown")

        self._media_position = int(status.get("curpos", 0)) // 1000
        total = int(status.get("totlen", 0))
        self._media_duration = total // 1000 if total > 0 else 0

        if self._state in ("PLAYING", "PAUSED"):
            await self._update_metadata()

    async def _update_metadata(self) -> None:
        if not self._client:
            return
        meta = await self._client.get_track_metadata()
        if not meta:
            return

        self._media_title = WiiMClient.clean_metadata_value(meta.get("title"))
        self._media_artist = WiiMClient.clean_metadata_value(meta.get("artist"))
        self._media_album = WiiMClient.clean_metadata_value(meta.get("album"))
        self._media_image_url = WiiMClient.clean_metadata_value(meta.get("albumArtURI"))

        if self._media_artist or self._media_album:
            self._media_type = "MUSIC"
        elif self._media_title and self._media_image_url:
            self._media_type = "RADIO"
        else:
            self._media_type = "MUSIC"

    def _clear_media(self) -> None:
        self._media_title = None
        self._media_artist = None
        self._media_album = None
        self._media_image_url = None
        self._media_duration = 0
        self._media_position = 0

    def _build_source_list(self) -> None:
        sources = list(PHYSICAL_SOURCES.values())
        sources.extend(self._music_services)
        self._source_list = sources

    def _resolve_source_key(self, source_name: str) -> str | None:
        for key, name in PHYSICAL_SOURCES.items():
            if name == source_name:
                return key
        if source_name in self._music_services:
            return source_name
        return None

    async def _activate_service_preset(self, service_name: str) -> bool:
        for i, preset in enumerate(self._presets, start=1):
            if preset.get("source", "") == service_name:
                return await self._client.activate_preset(i)
        _LOG.warning("[%s] No preset found for service: %s", self.log_id, service_name)
        return False

    def _get_output_mode_id(self, output_name: str) -> str | None:
        for mode_id, name in self._audio_outputs.items():
            if name == output_name:
                return mode_id
        return None

    @staticmethod
    def _extract_music_services(presets: list[dict]) -> list[str]:
        seen: set[str] = set()
        services: list[str] = []
        for preset in presets:
            source = preset.get("source", "")
            if source and source not in seen:
                seen.add(source)
                services.append(source)
        return services
