"""
WiiM Select entities.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import select, StatusCodes
from ucapi_framework import SelectEntity

from uc_intg_wiim.config import WiiMDeviceConfig
from uc_intg_wiim.device import WiiMDevice

_LOG = logging.getLogger(__name__)


class WiiMEQSelect(SelectEntity):
    """Select entity for choosing an EQ preset."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"select.{device_config.identifier}.eq"

        super().__init__(
            entity_id,
            f"{device_config.name} Equalizer",
            attributes={
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.OPTIONS: [],
                select.Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({select.Attributes.STATE: select.States.UNAVAILABLE})
            return

        options_list = ["Off"] + list(self._device.eq_presets) if self._device.eq_presets else ["Off"]
        self.update({
            select.Attributes.STATE: select.States.ON,
            select.Attributes.OPTIONS: options_list,
            select.Attributes.CURRENT_OPTION: self._device.current_eq or "Off",
        })

    async def _handle_command(
        self, entity: select.Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s params=%s", self.id, cmd_id, params)
        try:
            if cmd_id == select.Commands.SELECT_OPTION:
                option = params.get("option", "") if params else ""
                if await self._device.cmd_set_eq(option):
                    return StatusCodes.OK
                return StatusCodes.SERVER_ERROR

            if cmd_id == select.Commands.SELECT_NEXT:
                return await self._cycle_option(1)

            if cmd_id == select.Commands.SELECT_PREVIOUS:
                return await self._cycle_option(-1)

            return StatusCodes.NOT_IMPLEMENTED
        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _cycle_option(self, direction: int) -> StatusCodes:
        options = ["Off"] + list(self._device.eq_presets)
        if not options:
            return StatusCodes.SERVER_ERROR
        current = self._device.current_eq or "Off"
        try:
            idx = options.index(current)
        except ValueError:
            idx = 0
        new_idx = (idx + direction) % len(options)
        if await self._device.cmd_set_eq(options[new_idx]):
            return StatusCodes.OK
        return StatusCodes.SERVER_ERROR


class WiiMAudioOutputSelect(SelectEntity):
    """Select entity for choosing audio output mode."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"select.{device_config.identifier}.output"

        super().__init__(
            entity_id,
            f"{device_config.name} Audio Output",
            attributes={
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.OPTIONS: [],
                select.Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({select.Attributes.STATE: select.States.UNAVAILABLE})
            return

        options_list = list(self._device.audio_outputs.values()) if self._device.audio_outputs else []
        self.update({
            select.Attributes.STATE: select.States.ON,
            select.Attributes.OPTIONS: options_list,
            select.Attributes.CURRENT_OPTION: self._device.current_audio_output or "",
        })

    async def _handle_command(
        self, entity: select.Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s params=%s", self.id, cmd_id, params)
        try:
            if cmd_id == select.Commands.SELECT_OPTION:
                option = params.get("option", "") if params else ""
                if await self._device.cmd_set_audio_output(option):
                    return StatusCodes.OK
                return StatusCodes.SERVER_ERROR

            if cmd_id == select.Commands.SELECT_NEXT:
                return await self._cycle_option(1)

            if cmd_id == select.Commands.SELECT_PREVIOUS:
                return await self._cycle_option(-1)

            return StatusCodes.NOT_IMPLEMENTED
        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _cycle_option(self, direction: int) -> StatusCodes:
        options = list(self._device.audio_outputs.values())
        if not options:
            return StatusCodes.SERVER_ERROR
        current = self._device.current_audio_output or ""
        try:
            idx = options.index(current)
        except ValueError:
            idx = 0
        new_idx = (idx + direction) % len(options)
        if await self._device.cmd_set_audio_output(options[new_idx]):
            return StatusCodes.OK
        return StatusCodes.SERVER_ERROR
