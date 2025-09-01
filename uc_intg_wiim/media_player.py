"""
WiiM Media Player Entity Implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any, Optional

from ucapi import StatusCodes
from ucapi.media_player import (
    Attributes, Commands, DeviceClasses, Features, 
    MediaPlayer, MediaType, States
)

_LOG = logging.getLogger(__name__)

class WiiMMediaPlayer(MediaPlayer):
    """WiiM Media Player entity implementation."""

    def __init__(self, device_id: str, device_name: str):
        """Initialize media player entity."""
        features = self._build_features()
        attributes = self._build_initial_attributes()
        
        super().__init__(
            identifier=f"{device_id}_media_player",
            name=device_name,
            features=features,
            attributes=attributes,
            device_class=DeviceClasses.STREAMING_BOX,
            cmd_handler=self._handle_command,
        )
        
        self._client = None
        self._integration_api = None
        self._initialized = False
        self._last_mode = None  # Track the last mode to detect source switches
        self._metadata_clear_pending = False  # Flag to force clear on next update

    def set_client(self, client):
        """Set the WiiM client."""
        self._client = client

    def _build_features(self) -> list:
        """Build media player features list."""
        return [
            Features.ON_OFF, Features.VOLUME, Features.VOLUME_UP_DOWN,
            Features.MUTE_TOGGLE, Features.MUTE, Features.UNMUTE,
            Features.PLAY_PAUSE, Features.STOP, Features.NEXT, Features.PREVIOUS,
            Features.REPEAT, Features.SHUFFLE, Features.MEDIA_DURATION,
            Features.MEDIA_POSITION, Features.MEDIA_TITLE, Features.MEDIA_ARTIST,
            Features.MEDIA_ALBUM, Features.MEDIA_IMAGE_URL, Features.MEDIA_TYPE,
            Features.SELECT_SOURCE,  # Added for activity source selection
        ]

    def _build_initial_attributes(self) -> dict:
        """Build initial attributes dictionary."""
        return {
            Attributes.STATE: States.STANDBY,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.SOURCE_LIST: [],  # Will be populated during initialization
            Attributes.SOURCE: None,     # Will be set based on current mode
        }

    async def initialize_and_set_state(self):
        """Initialize capabilities and set initial state."""
        if not self._client:
            return
        
        # Set up comprehensive source list for activity integration (inputs + outputs)
        source_list = []
        
        # Add input sources
        if self._client.sources:
            source_list.extend(list(self._client.sources.keys()))
        
        # Add output routing options
        output_sources = [
            'line-out',      # Line output
            'headphone',     # Headphone output
            'optical-out',   # Optical output
            'coax-out',      # Coaxial output
            'bluetooth-out', # Bluetooth output (for devices that support it)
            'multi-room'     # Multi-room output
        ]
        source_list.extend(output_sources)
        
        self.attributes[Attributes.SOURCE_LIST] = source_list
        _LOG.info("Initialized source list for activities (inputs + outputs): %s", source_list)
        
        await self.update_attributes()
        self._initialized = True
        _LOG.info("Media Player initialized with comprehensive source selection capability")

    async def update_attributes(self):
        """Update entity attributes from device state."""
        if not self._client:
            return
            
        try:
            status = await self._client.get_player_status()
            if not status:
                self._handle_state_update(States.UNAVAILABLE)
                return

            self._update_basic_attributes(status)
            await self._update_playback_state(status)
            self._update_source_info(status)
            self._force_integration_update()
                
        except Exception as e:
            _LOG.error("Error updating media player state: %s", e)
            self._clear_media_info()
            self._handle_state_update(States.UNAVAILABLE)

    def _update_basic_attributes(self, status: dict):
        """Update basic playback attributes."""
        self.attributes[Attributes.VOLUME] = int(status.get('vol', 0))
        self.attributes[Attributes.MUTED] = status.get('mute', '0') == '1'
        self.attributes[Attributes.REPEAT] = self._parse_repeat_mode(status.get('loop', '0'))
        self.attributes[Attributes.SHUFFLE] = status.get('loop', '0') in ['2', '3']

    async def _update_playback_state(self, status: dict):
        """Update playback state and media information."""
        player_status = status.get('status', 'stop').lower()
        current_mode = int(status.get('mode', 0))
        
        # Check if source/mode has changed or if we need to force clear
        if (self._last_mode is not None and self._last_mode != current_mode) or self._metadata_clear_pending:
            _LOG.debug("Source changed from mode %s to %s or force clear requested, clearing old metadata", 
                      self._last_mode, current_mode)
            self._clear_media_info()
            self._metadata_clear_pending = False
            # Wait a moment for device to stabilize before getting new metadata
            await asyncio.sleep(0.5)
        
        self._last_mode = current_mode
        
        _LOG.debug("Player status: %s, Mode: %s", player_status, current_mode)
        
        if player_status in ['play', 'loading']:
            await self._update_media_info(status)
            self._handle_state_update(States.PLAYING)
        elif player_status == 'pause':
            await self._update_media_info(status)
            self._handle_state_update(States.PAUSED)
        elif player_status == 'stop':
            self._clear_media_info()
            self._handle_state_update(States.STANDBY)
        else:
            self._clear_media_info()
            self._handle_state_update(States.STANDBY)

    def _update_source_info(self, status: dict):
        """Update current source based on mode."""
        mode = int(status.get('mode', 0))
        source_map = {
            31: 'wifi',        # Spotify Connect
            32: 'wifi',        # TIDAL Connect  
            40: 'line-in',     # AUX-In
            41: 'bluetooth',   # Bluetooth
            43: 'optical',     # Optical
            10: 'wifi',        # Network modes
            11: 'wifi',
            16: 'wifi'
        }
        
        if mode in source_map:
            self.attributes[Attributes.SOURCE] = source_map[mode]

    def _clear_media_info(self):
        """Clear media information attributes."""
        media_attrs = [
            Attributes.MEDIA_TITLE, Attributes.MEDIA_ARTIST, Attributes.MEDIA_ALBUM,
            Attributes.MEDIA_IMAGE_URL, Attributes.MEDIA_DURATION, 
            Attributes.MEDIA_POSITION, Attributes.MEDIA_TYPE
        ]
        for attr in media_attrs:
            self.attributes.pop(attr, None)
        _LOG.debug("Cleared media information attributes")

    async def _update_media_info(self, player_status: dict):
        """Update media information from metadata."""
        try:
            metadata = await self._client.get_track_metadata()
            if not metadata:
                # If no metadata available, clear existing media info to prevent stale data
                self._clear_media_info()
                return
                
            # Only update if we have valid metadata
            if self._has_valid_metadata(metadata):
                self._set_media_metadata(metadata)
                self._set_position_duration(player_status)
                self._set_media_type(player_status)
            else:
                # Clear media info if metadata is not valid/useful
                self._clear_media_info()
                
        except Exception as e:
            _LOG.error("Error updating media info: %s", e)
            self._clear_media_info()

    def _has_valid_metadata(self, metadata: dict) -> bool:
        """Check if metadata contains useful information."""
        title = self._clean_metadata(metadata.get('title'))
        artist = self._clean_metadata(metadata.get('artist'))
        album = self._clean_metadata(metadata.get('album'))
        
        # Consider metadata valid if we have at least a title or artist
        return bool(title or artist or album)

    def _set_media_metadata(self, metadata: dict):
        """Set media metadata attributes."""
        if title := self._clean_metadata(metadata.get('title')):
            self.attributes[Attributes.MEDIA_TITLE] = title
            
        if artist := self._clean_metadata(metadata.get('artist')):
            self.attributes[Attributes.MEDIA_ARTIST] = artist
            
        if album := self._clean_metadata(metadata.get('album')):
            self.attributes[Attributes.MEDIA_ALBUM] = album
            
        if image_url := self._clean_metadata(metadata.get('albumArtURI')):
            self.attributes[Attributes.MEDIA_IMAGE_URL] = image_url

    def _set_position_duration(self, player_status: dict):
        """Set position and duration attributes."""
        if 'totlen' in player_status:
            duration = int(player_status['totlen']) // 1000
            if duration > 0:
                self.attributes[Attributes.MEDIA_DURATION] = duration
                
        if 'curpos' in player_status:
            position = int(player_status['curpos']) // 1000
            self.attributes[Attributes.MEDIA_POSITION] = position

    def _set_media_type(self, player_status: dict):
        """Set media type based on mode."""
        mode = int(player_status.get('mode', 0))
        if mode in [31, 32, 10, 11, 16]:  # Music streaming modes
            self.attributes[Attributes.MEDIA_TYPE] = MediaType.MUSIC

    def _clean_metadata(self, value: Optional[str]) -> Optional[str]:
        """Clean metadata values."""
        if not value or value.lower() in ['unknow', 'un_known', 'unknown', '']:
            return None
        return value.strip()

    def _handle_state_update(self, new_state: States):
        """Update state and notify integration API."""
        if new_state != self.attributes.get(Attributes.STATE):
            self.attributes[Attributes.STATE] = new_state
            _LOG.debug("Media player state changed to: %s", new_state)

    def _force_integration_update(self):
        """Force update to integration API."""
        if self._integration_api and hasattr(self._integration_api, 'configured_entities'):
            try:
                self._integration_api.configured_entities.update_attributes(
                    self.id, self.attributes
                )
            except Exception as e:
                _LOG.debug("Could not update integration API: %s", e)

    def _parse_repeat_mode(self, loop_mode: str) -> str:
        """Parse loop mode to repeat mode."""
        mode_map = {
            '0': 'off',    # loop all
            '1': 'one',    # single loop
            '2': 'all',    # shuffle loop
            '3': 'off',    # shuffle, no loop
            '4': 'off'     # no shuffle, no loop
        }
        return mode_map.get(str(loop_mode), 'off')

    async def _handle_command(self, entity, cmd_id: str, params: dict = None) -> StatusCodes:
        """Handle media player commands."""
        if not self._client:
            return StatusCodes.SERVER_ERROR
            
        try:
            _LOG.info("Handling command: %s with params: %s", cmd_id, params)
            
            command_map = {
                Commands.ON: self._client.resume_playback,
                Commands.OFF: self._client.stop_playback,
                Commands.TOGGLE: self._client.toggle_playback,
                Commands.PLAY_PAUSE: self._client.toggle_playback,
                Commands.STOP: self._client.stop_playback,
                Commands.PREVIOUS: self._client.previous_track,
                Commands.NEXT: self._client.next_track,
                Commands.VOLUME_UP: self._client.volume_up,
                Commands.VOLUME_DOWN: self._client.volume_down,
                Commands.MUTE_TOGGLE: self._client.toggle_mute,
                Commands.MUTE: lambda: self._client.set_mute(True),
                Commands.UNMUTE: lambda: self._client.set_mute(False),
            }
            
            if cmd_id in command_map:
                await command_map[cmd_id]()
            elif cmd_id == Commands.VOLUME and params and 'volume' in params:
                await self._client.set_volume(int(params['volume']))
            elif cmd_id == Commands.SELECT_SOURCE and params and 'source' in params:
                source = params['source']
                _LOG.info("Switching to source: %s", source)
                
                # Set flag to clear metadata on next update
                self._metadata_clear_pending = True
                
                # Handle different types of source/output switching
                if source.endswith('-out') or source in ['headphone', 'multi-room', 'bluetooth-out']:
                    # Output routing command
                    await self._handle_output_routing(source)
                else:
                    # Input source switching
                    await self._client.send_command(f"setPlayerCmd:switchmode:{source}")
                
                # Force immediate state update after source change
                asyncio.create_task(self._immediate_update_after_source_change())
            else:
                _LOG.warning("Unhandled command: %s", cmd_id)
                return StatusCodes.NOT_IMPLEMENTED
            
            asyncio.create_task(self._deferred_update())
            return StatusCodes.OK
            
        except Exception as e:
            _LOG.error("Error handling command %s: %s", cmd_id, e)
            return StatusCodes.SERVER_ERROR

    async def _immediate_update_after_source_change(self):
        """Immediate update after source change to clear stale metadata faster."""
        await asyncio.sleep(0.5)  # Brief wait for device to process command
        await self.update_attributes()

    async def _handle_output_routing(self, output: str):
        """Handle output routing commands for WiiM device."""
        try:
            # Map output names to WiiM API commands
            output_commands = {
                'line-out': 'setAudioOutput:line',
                'headphone': 'setAudioOutput:headphone', 
                'optical-out': 'setAudioOutput:optical',
                'coax-out': 'setAudioOutput:coax',
                'bluetooth-out': 'setAudioOutput:bluetooth',
                'multi-room': 'setPlayerCmd:multiroom:on'  # Multi-room mode
            }
            
            if output in output_commands:
                command = output_commands[output]
                _LOG.info("Executing output routing command: %s", command)
                await self._client.send_command(command)
            else:
                _LOG.warning("Unknown output routing option: %s", output)
                
        except Exception as e:
            _LOG.error("Error setting output routing %s: %s", output, e)

    async def _deferred_update(self):
        """Update attributes after a short delay."""
        await asyncio.sleep(1.0)
        await self.update_attributes()