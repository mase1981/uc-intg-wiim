"""
WiiM Media Player entity.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import media_player, StatusCodes
from ucapi.api_definitions import (
    BrowseOptions,
    BrowseResults,
    SearchOptions,
    SearchResults,
)
from ucapi_framework import MediaPlayerEntity, MediaPlayerAttributes

from uc_intg_wiim import browser
from uc_intg_wiim.config import WiiMDeviceConfig
from uc_intg_wiim.device import WiiMDevice

_LOG = logging.getLogger(__name__)

FEATURES = [
    media_player.Features.VOLUME,
    media_player.Features.VOLUME_UP_DOWN,
    media_player.Features.MUTE_TOGGLE,
    media_player.Features.MUTE,
    media_player.Features.UNMUTE,
    media_player.Features.PLAY_PAUSE,
    media_player.Features.STOP,
    media_player.Features.NEXT,
    media_player.Features.PREVIOUS,
    media_player.Features.REPEAT,
    media_player.Features.SHUFFLE,
    media_player.Features.MEDIA_DURATION,
    media_player.Features.MEDIA_POSITION,
    media_player.Features.MEDIA_TITLE,
    media_player.Features.MEDIA_ARTIST,
    media_player.Features.MEDIA_ALBUM,
    media_player.Features.MEDIA_IMAGE_URL,
    media_player.Features.MEDIA_TYPE,
    media_player.Features.SELECT_SOURCE,
    media_player.Features.PLAY_MEDIA,
    media_player.Features.BROWSE_MEDIA,
    media_player.Features.SEARCH_MEDIA,
]


class WiiMMediaPlayer(MediaPlayerEntity):
    """Media player entity for WiiM devices."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"media_player.{device_config.identifier}"

        super().__init__(
            entity_id,
            device_config.name,
            features=FEATURES,
            attributes={
                media_player.Attributes.STATE: media_player.States.UNAVAILABLE,
                media_player.Attributes.VOLUME: 0,
                media_player.Attributes.MUTED: False,
                media_player.Attributes.SOURCE: "",
                media_player.Attributes.SOURCE_LIST: [],
            },
            device_class=media_player.DeviceClasses.SPEAKER,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = self.map_entity_states(self._device.state)
        attrs = MediaPlayerAttributes(
            STATE=state,
            VOLUME=self._device.volume,
            MUTED=self._device.muted,
            SOURCE=self._device.source,
            SOURCE_LIST=self._device.source_list,
            REPEAT=self._device.repeat_mode,
            SHUFFLE=self._device.shuffle,
            MEDIA_TITLE=self._device.media_title or "",
            MEDIA_ARTIST=self._device.media_artist or "",
            MEDIA_ALBUM=self._device.media_album or "",
            MEDIA_IMAGE_URL=self._device.media_image_url or "",
            MEDIA_DURATION=self._device.media_duration,
            MEDIA_POSITION=self._device.media_position,
            MEDIA_TYPE=self._device.media_type,
        )
        self.update(attrs)

    async def browse(self, options: BrowseOptions) -> BrowseResults | StatusCodes:
        return await browser.browse(self._device, options)

    async def search(self, options: SearchOptions) -> SearchResults | StatusCodes:
        return await browser.search(self._device, options)

    async def _handle_command(
        self, entity: media_player.MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s params=%s", self.id, cmd_id, params)

        try:
            result = await self._dispatch_command(cmd_id, params)
            return StatusCodes.OK if result else StatusCodes.SERVER_ERROR
        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _dispatch_command(
        self, cmd_id: str, params: dict[str, Any] | None
    ) -> bool:
        if cmd_id == media_player.Commands.PLAY_PAUSE:
            return await self._device.cmd_play_pause()
        if cmd_id == media_player.Commands.STOP:
            return await self._device.cmd_stop()
        if cmd_id == media_player.Commands.NEXT:
            return await self._device.cmd_next()
        if cmd_id == media_player.Commands.PREVIOUS:
            return await self._device.cmd_previous()
        if cmd_id == media_player.Commands.VOLUME:
            if params and "volume" in params:
                return await self._device.cmd_set_volume(int(params["volume"]))
            return False
        if cmd_id == media_player.Commands.VOLUME_UP:
            return await self._device.cmd_volume_up()
        if cmd_id == media_player.Commands.VOLUME_DOWN:
            return await self._device.cmd_volume_down()
        if cmd_id == media_player.Commands.MUTE_TOGGLE:
            return await self._device.cmd_mute_toggle()
        if cmd_id == media_player.Commands.MUTE:
            return await self._device.cmd_mute(True)
        if cmd_id == media_player.Commands.UNMUTE:
            return await self._device.cmd_mute(False)
        if cmd_id == media_player.Commands.SELECT_SOURCE:
            if params and "source" in params:
                return await self._device.cmd_select_source(params["source"])
            return False
        if cmd_id == media_player.Commands.PLAY_MEDIA:
            return await self._handle_play_media(params)
        if cmd_id == media_player.Commands.TOGGLE:
            return await self._device.cmd_play_pause()

        _LOG.warning("[%s] Unhandled command: %s", self.id, cmd_id)
        return False

    async def _handle_play_media(self, params: dict[str, Any] | None) -> bool:
        if not params:
            return False
        media_id = params.get("media_id", "")
        if not media_id:
            return False

        if media_id.startswith("preset_"):
            try:
                preset_num = int(media_id[7:])
                return await self._device.cmd_activate_preset(preset_num)
            except ValueError:
                return False

        if media_id.startswith("source_"):
            source_name = media_id[7:]
            return await self._device.cmd_select_source(source_name)

        _LOG.warning("[%s] Unknown media_id: %s", self.id, media_id)
        return False
