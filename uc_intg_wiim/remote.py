"""
WiiM Remote entity with custom UI pages.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import remote, StatusCodes
from ucapi.ui import (
    Buttons,
    UiPage,
    Size,
    create_btn_mapping,
    create_ui_icon,
    create_ui_text,
)
from ucapi_framework import RemoteEntity

from uc_intg_wiim.config import WiiMDeviceConfig
from uc_intg_wiim.device import WiiMDevice

_LOG = logging.getLogger(__name__)


class WiiMRemote(RemoteEntity):
    """Remote entity for WiiM devices with custom UI pages."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"remote.{device_config.identifier}"

        simple_commands, ui_pages, button_mapping = self._build_remote_ui(device)

        super().__init__(
            entity_id,
            device_config.name,
            features=[remote.Features.SEND_CMD],
            attributes={remote.Attributes.STATE: remote.States.UNKNOWN},
            simple_commands=simple_commands,
            button_mapping=button_mapping,
            ui_pages=ui_pages,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({remote.Attributes.STATE: remote.States.UNAVAILABLE})
            return
        self.update({remote.Attributes.STATE: remote.States.ON})

    async def _handle_command(
        self, entity: remote.Remote, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != remote.Commands.SEND_CMD:
            return StatusCodes.NOT_IMPLEMENTED

        command = params.get("command", "") if params else ""
        if not command:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Send command: %s", self.id, command)

        try:
            result = await self._dispatch_command(command)
            return StatusCodes.OK if result else StatusCodes.SERVER_ERROR
        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _dispatch_command(self, command: str) -> bool:
        if command == "play":
            return await self._device.cmd_play_pause()
        if command == "pause":
            return await self._device.cmd_play_pause()
        if command == "stop":
            return await self._device.cmd_stop()
        if command == "next":
            return await self._device.cmd_next()
        if command == "previous":
            return await self._device.cmd_previous()
        if command == "volume_up":
            return await self._device.cmd_volume_up()
        if command == "volume_down":
            return await self._device.cmd_volume_down()
        if command == "mute_toggle":
            return await self._device.cmd_mute_toggle()
        if command == "display_on":
            return await self._device.cmd_display_on()
        if command == "display_off":
            return await self._device.cmd_display_off()
        if command == "reboot":
            return await self._device.cmd_reboot()

        if command.startswith("source_"):
            source_name = command[7:]
            return await self._device.cmd_select_source(source_name)

        if command.startswith("preset_"):
            try:
                preset_num = int(command[7:])
                return await self._device.cmd_activate_preset(preset_num)
            except ValueError:
                pass

        if command.startswith("eq_"):
            preset_name = command[3:]
            if preset_name == "off":
                return await self._device.cmd_set_eq("Off")
            return await self._device.cmd_set_eq(preset_name)

        if command.startswith("output_"):
            output_name = command[7:]
            return await self._device.cmd_set_audio_output(output_name)

        _LOG.warning("[%s] Unknown command: %s", self.id, command)
        return False

    def _build_remote_ui(
        self, device: WiiMDevice
    ) -> tuple[list[str], list[UiPage], list]:
        simple_commands: list[str] = []
        pages: list[UiPage] = []

        pages.append(self._build_main_controls_page(simple_commands))
        pages.append(self._build_sources_page(device, simple_commands))

        if device.presets:
            pages.append(self._build_presets_page(device, simple_commands))

        if device.audio_outputs:
            pages.append(self._build_audio_output_page(device, simple_commands))

        if device.eq_presets:
            pages.append(self._build_eq_page(device, simple_commands))

        pages.append(self._build_device_control_page(simple_commands))

        button_mapping = self._build_button_mapping()

        return simple_commands, pages, button_mapping

    @staticmethod
    def _build_main_controls_page(cmds: list[str]) -> UiPage:
        page = UiPage("main", "Playback", grid=Size(4, 6))
        for cmd in ["play", "pause", "stop", "next", "previous", "volume_up", "volume_down", "mute_toggle"]:
            if cmd not in cmds:
                cmds.append(cmd)

        page.add(create_ui_icon("uc:prev", 0, 0, cmd="previous"))
        page.add(create_ui_icon("uc:play", 1, 0, cmd="play"))
        page.add(create_ui_icon("uc:pause", 2, 0, cmd="pause"))
        page.add(create_ui_icon("uc:next", 3, 0, cmd="next"))

        page.add(create_ui_icon("uc:vol-down", 0, 1, cmd="volume_down"))
        page.add(create_ui_icon("uc:vol-up", 1, 1, cmd="volume_up"))
        page.add(create_ui_icon("uc:mute", 2, 1, cmd="mute_toggle"))
        page.add(create_ui_icon("uc:stop", 3, 1, cmd="stop"))

        return page

    @staticmethod
    def _build_sources_page(device: WiiMDevice, cmds: list[str]) -> UiPage:
        page = UiPage("sources", "Sources", grid=Size(4, 6))
        row, col = 0, 0

        source_icons = {
            "WiFi": "uc:wifi",
            "Bluetooth": "uc:bluetooth",
            "Line In": "uc:input",
            "Optical": "uc:input",
            "HDMI": "uc:hdmi",
            "USB": "uc:usb",
        }

        all_sources = list(device.source_list)
        for source_name in all_sources:
            cmd = f"source_{source_name}"
            if cmd not in cmds:
                cmds.append(cmd)

            icon = source_icons.get(source_name)
            if icon:
                page.add(create_ui_icon(icon, col, row, cmd=cmd))
            else:
                label = source_name[:8]
                page.add(create_ui_text(label, col, row, cmd=cmd))

            col += 1
            if col >= 4:
                col = 0
                row += 1
            if row >= 6:
                break

        return page

    @staticmethod
    def _build_presets_page(device: WiiMDevice, cmds: list[str]) -> UiPage:
        page = UiPage("presets", "Presets", grid=Size(4, 6))
        row, col = 0, 0

        for i, preset in enumerate(device.presets[:12], start=1):
            cmd = f"preset_{i}"
            if cmd not in cmds:
                cmds.append(cmd)

            name = preset.get("name", f"#{i}")
            label = f"{i}: {name[:6]}"
            page.add(create_ui_text(label, col, row, cmd=cmd))

            col += 1
            if col >= 4:
                col = 0
                row += 1

        return page

    @staticmethod
    def _build_audio_output_page(device: WiiMDevice, cmds: list[str]) -> UiPage:
        page = UiPage("output", "Audio Output", grid=Size(4, 6))
        row, col = 0, 0

        for mode_name in device.audio_outputs.values():
            cmd = f"output_{mode_name}"
            if cmd not in cmds:
                cmds.append(cmd)

            label = mode_name[:8]
            page.add(create_ui_text(label, col, row, cmd=cmd))

            col += 1
            if col >= 4:
                col = 0
                row += 1

        return page

    @staticmethod
    def _build_eq_page(device: WiiMDevice, cmds: list[str]) -> UiPage:
        page = UiPage("eq", "Equalizer", grid=Size(4, 6))

        cmd_off = "eq_off"
        if cmd_off not in cmds:
            cmds.append(cmd_off)
        page.add(create_ui_text("EQ Off", 0, 0, cmd=cmd_off))

        row, col = 0, 1
        for preset_name in device.eq_presets[:14]:
            cmd = f"eq_{preset_name}"
            if cmd not in cmds:
                cmds.append(cmd)

            label = preset_name[:8]
            page.add(create_ui_text(label, col, row, cmd=cmd))

            col += 1
            if col >= 4:
                col = 0
                row += 1

        return page

    @staticmethod
    def _build_device_control_page(cmds: list[str]) -> UiPage:
        page = UiPage("device", "Device", grid=Size(4, 6))

        for cmd in ["display_on", "display_off", "reboot"]:
            if cmd not in cmds:
                cmds.append(cmd)

        page.add(create_ui_text("Disp ON", 0, 0, cmd="display_on"))
        page.add(create_ui_text("Disp OFF", 1, 0, cmd="display_off"))
        page.add(create_ui_text("REBOOT", 2, 0, cmd="reboot"))

        return page

    @staticmethod
    def _build_button_mapping() -> list:
        return [
            create_btn_mapping(Buttons.PLAY, short="play"),
            create_btn_mapping(Buttons.PREV, short="previous"),
            create_btn_mapping(Buttons.NEXT, short="next"),
            create_btn_mapping(Buttons.VOLUME_UP, short="volume_up"),
            create_btn_mapping(Buttons.VOLUME_DOWN, short="volume_down"),
            create_btn_mapping(Buttons.MUTE, short="mute_toggle"),
            create_btn_mapping(Buttons.POWER, short="stop", long="reboot"),
            create_btn_mapping(Buttons.BACK, short="stop"),
            create_btn_mapping(Buttons.HOME, short="play"),
            create_btn_mapping(Buttons.DPAD_UP, short="volume_up"),
            create_btn_mapping(Buttons.DPAD_DOWN, short="volume_down"),
            create_btn_mapping(Buttons.DPAD_LEFT, short="previous"),
            create_btn_mapping(Buttons.DPAD_RIGHT, short="next"),
            create_btn_mapping(Buttons.DPAD_MIDDLE, short="play"),
        ]
