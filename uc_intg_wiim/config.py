"""
Configuration management for WiiM integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass, field


@dataclass
class WiiMDeviceConfig:
    """WiiM device configuration."""

    identifier: str
    name: str
    host: str
    eq_presets: list[str] = field(default_factory=list)
    presets: list[dict] = field(default_factory=list)
    audio_outputs: dict[str, str] = field(default_factory=dict)
    music_services: list[str] = field(default_factory=list)
