"""
WiiM Integration Driver.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi_framework import BaseIntegrationDriver

from uc_intg_wiim.config import WiiMDeviceConfig
from uc_intg_wiim.device import WiiMDevice
from uc_intg_wiim.media_player import WiiMMediaPlayer
from uc_intg_wiim.remote import WiiMRemote
from uc_intg_wiim.select import WiiMAudioOutputSelect, WiiMEQSelect
from uc_intg_wiim.sensor import (
    WiiMCurrentSourceSensor,
    WiiMDeviceModelSensor,
    WiiMFirmwareSensor,
    WiiMIPAddressSensor,
    WiiMWiFiSensor,
)

_LOG = logging.getLogger(__name__)


class WiiMDriver(BaseIntegrationDriver[WiiMDevice, WiiMDeviceConfig]):
    """Integration driver for WiiM audio devices."""

    def __init__(self) -> None:
        super().__init__(
            device_class=WiiMDevice,
            entity_classes=[
                WiiMMediaPlayer,
                WiiMRemote,
                WiiMFirmwareSensor,
                WiiMDeviceModelSensor,
                WiiMWiFiSensor,
                WiiMIPAddressSensor,
                WiiMCurrentSourceSensor,
                lambda cfg, dev: WiiMEQSelect(cfg, dev) if dev.eq_presets else None,
                lambda cfg, dev: WiiMAudioOutputSelect(cfg, dev) if dev.audio_outputs else None,
            ],
            driver_id="uc-intg-wiim",
            require_connection_before_registry=True,
        )
