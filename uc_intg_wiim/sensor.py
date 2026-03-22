"""
WiiM Sensor entities.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_wiim.config import WiiMDeviceConfig
from uc_intg_wiim.device import WiiMDevice

_LOG = logging.getLogger(__name__)


class WiiMFirmwareSensor(SensorEntity):
    """Sensor showing the WiiM device firmware version."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.firmware"

        super().__init__(
            entity_id,
            f"{device_config.name} Firmware",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.firmware or "Unknown",
        })


class WiiMDeviceModelSensor(SensorEntity):
    """Sensor showing the WiiM device hardware/model info."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.model"

        super().__init__(
            entity_id,
            f"{device_config.name} Model",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.hardware or "Unknown",
        })


class WiiMWiFiSensor(SensorEntity):
    """Sensor showing the WiFi SSID the WiiM device is connected to."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.wifi"

        super().__init__(
            entity_id,
            f"{device_config.name} WiFi",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.wifi_ssid or "Unknown",
        })


class WiiMIPAddressSensor(SensorEntity):
    """Sensor showing the WiiM device IP address."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.ip"

        super().__init__(
            entity_id,
            f"{device_config.name} IP Address",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.ip_address or self._device.address,
        })


class WiiMCurrentSourceSensor(SensorEntity):
    """Sensor showing what source/mode the WiiM is currently using."""

    def __init__(self, device_config: WiiMDeviceConfig, device: WiiMDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.source"

        super().__init__(
            entity_id,
            f"{device_config.name} Current Source",
            features=[],
            attributes={
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: "",
            },
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: self._device.source or "Idle",
        })
