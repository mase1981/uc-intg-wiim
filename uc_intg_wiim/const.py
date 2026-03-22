"""
Constants and mappings for WiiM integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

WIIM_API_PORT = 443
WIIM_API_TIMEOUT = 5
WIIM_THROTTLE_DELAY = 0.2
WIIM_POLL_INTERVAL = 5
WIIM_CONNECTION_CHECK_INTERVAL = 30

VOLUME_STEP = 5

PHYSICAL_SOURCES = {
    "wifi": "WiFi",
    "bluetooth": "Bluetooth",
    "line-in": "Line In",
    "optical": "Optical",
    "HDMI": "HDMI",
    "phono": "Phono",
    "udisk": "USB",
}

AUDIO_OUTPUT_MODES = {
    "1": "SPDIF",
    "2": "AUX/Line Out",
    "3": "COAX",
}

PLAYBACK_MODE_MAP = {
    "-1": "Idle",
    "0": "Idle",
    "1": "AirPlay",
    "2": "DLNA",
    "10": "WiiM",
    "11": "USB Disk",
    "16": "TF Card",
    "31": "Spotify Connect",
    "32": "TIDAL Connect",
    "40": "AUX-In",
    "41": "Bluetooth",
    "42": "External Storage",
    "43": "Optical-In",
    "50": "Mirror",
    "60": "Voice Mail",
    "99": "Slave",
}

LOOP_MODE_MAP = {
    "0": "OFF",
    "1": "ONE",
    "2": "ALL",
    "3": "OFF",
    "4": "OFF",
}

UNKNOWN_METADATA_VALUES = {"unknow", "un_known", "unknown", ""}
