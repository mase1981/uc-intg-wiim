"""
WiiM Integration for Unfolded Circle Remote Two/3.

A professional integration for controlling WiiM audio streaming devices 
(Mini, Pro, Pro Plus, Ultra, Amp) with complete media player and remote control functionality.

:copyright: (c) 2025 by Meir Miyara.
:license: MIT, see LICENSE for more details.
"""

__version__ = "1.0.10"
__author__ = "Meir Miyara"
__email__ = "meir.miyara@gmail.com"
__license__ = "MIT"

from uc_intg_wiim.client import WiiMClient
from uc_intg_wiim.config import Config
from uc_intg_wiim.media_player import WiiMMediaPlayer
from uc_intg_wiim.remote import WiiMRemote

__all__ = [
    "WiiMClient",
    "Config", 
    "WiiMMediaPlayer",
    "WiiMRemote"
]
