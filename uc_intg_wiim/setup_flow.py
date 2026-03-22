"""
WiiM Setup Flow handler.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi.api_definitions import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_wiim.client import WiiMClient
from uc_intg_wiim.config import WiiMDeviceConfig

_LOG = logging.getLogger(__name__)


class WiiMSetupFlow(BaseSetupFlow[WiiMDeviceConfig]):
    """Setup flow for WiiM device configuration."""

    def get_manual_entry_form(self) -> RequestUserInput:
        """Return the manual entry form for WiiM device setup."""
        return RequestUserInput(
            {"en": "WiiM Device Setup"},
            [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": "WiiM"}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": ""}},
                },
            ],
        )

    async def query_device(self, input_values: dict[str, Any]) -> WiiMDeviceConfig:
        """Validate connection and discover capabilities."""
        host = input_values.get("host", "").strip()
        if not host:
            raise ValueError("IP address is required")

        name = input_values.get("name", "WiiM").strip() or "WiiM"

        client = WiiMClient(host)
        try:
            await client.connect()
            if not await asyncio.wait_for(client.test_connection(), timeout=10.0):
                raise ValueError(f"Cannot connect to WiiM device at {host}")

            info = await client.get_device_info()
            if info:
                device_name = info.get("DeviceName")
                if device_name and name == "WiiM":
                    name = device_name

            eq_presets = await client.get_eq_list() or []

            preset_info = await client.get_preset_info()
            presets = preset_info.get("preset_list", []) if preset_info else []

            music_services = self._extract_services(presets)

            audio_outputs = {}
            output_info = await client.get_audio_output_info()
            if output_info:
                from uc_intg_wiim.const import AUDIO_OUTPUT_MODES

                for mode_id, mode_name in AUDIO_OUTPUT_MODES.items():
                    audio_outputs[mode_id] = mode_name
                if output_info.get("source", "0") == "1":
                    audio_outputs["bt_source"] = "BT Source"
                if output_info.get("audiocast", "0") == "1":
                    audio_outputs["audiocast"] = "Audio Cast"
            else:
                audio_outputs = {"1": "SPDIF", "2": "AUX/Line Out", "3": "COAX"}

        except asyncio.TimeoutError:
            raise ValueError(f"Connection to {host} timed out") from None
        finally:
            await client.close()

        identifier = f"wiim_{host.replace('.', '_')}"

        return WiiMDeviceConfig(
            identifier=identifier,
            name=name,
            host=host,
            eq_presets=eq_presets,
            presets=presets,
            audio_outputs=audio_outputs,
            music_services=music_services,
        )

    @staticmethod
    def _extract_services(presets: list[dict]) -> list[str]:
        seen: set[str] = set()
        services: list[str] = []
        for preset in presets:
            source = preset.get("source", "")
            if source and source not in seen:
                seen.add(source)
                services.append(source)
        return services
