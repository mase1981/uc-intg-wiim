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
        self._last_mode = None
        self._last_status = None  # Track status changes too
        self._metadata_clear_pending = False
        self._last_meaningful_metadata = {}  # Track last meaningful metadata

    def set_client(self, client):
        """Set the WiiM client."""
        self._client = client

    def _build_features(self) -> list:
        """Build media player features list."""
        return [
            Features.VOLUME, Features.VOLUME_UP_DOWN,
            Features.MUTE_TOGGLE, Features.MUTE, Features.UNMUTE,
            Features.PLAY_PAUSE, Features.STOP, Features.NEXT, Features.PREVIOUS,
            Features.REPEAT, Features.SHUFFLE, Features.MEDIA_DURATION,
            Features.MEDIA_POSITION, Features.MEDIA_TITLE, Features.MEDIA_ARTIST,
            Features.MEDIA_ALBUM, Features.MEDIA_IMAGE_URL, Features.MEDIA_TYPE,
            Features.SELECT_SOURCE,
        ]

    def _build_initial_attributes(self) -> dict:
        """Build initial attributes dictionary."""
        return {
            Attributes.STATE: States.STANDBY,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.SOURCE_LIST: [],
            Attributes.SOURCE: None,
        }

    async def initialize_and_set_state(self):
        """Initialize capabilities and set initial state."""
        if not self._client:
            return
        
        source_list = []
        if self._client.sources:
            source_list.extend(list(self._client.sources.keys()))
        
        special_functions = [
            'display_on', 'display_off', 'reboot_device', 'toggle_display'
        ]
        source_list.extend(special_functions)
        
        self.attributes[Attributes.SOURCE_LIST] = source_list
        _LOG.info("Initialized source list: %s", source_list)
        
        await self.update_attributes()
        self._initialized = True

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
            self._clear_all_media_info()
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
        
        # CRITICAL FIX: Check for both mode changes AND status changes that indicate source switching
        mode_changed = self._last_mode is not None and self._last_mode != current_mode
        
        # Enhanced clearing logic: Clear when switching away from rich metadata sources
        needs_clearing = (
            mode_changed or 
            self._metadata_clear_pending or
            self._should_force_metadata_clear(current_mode, player_status)
        )
        
        if needs_clearing:
            _LOG.info("🧹 CLEARING METADATA - Mode: %s→%s, Status: %s→%s, Force: %s", 
                     self._last_mode, current_mode, self._last_status, player_status, 
                     self._metadata_clear_pending)
            self._clear_all_media_info()
            self._metadata_clear_pending = False
            await asyncio.sleep(0.3)  # Brief stabilization delay
        
        # Update tracking variables
        self._last_mode = current_mode
        self._last_status = player_status
        
        _LOG.debug("Player status: %s, Mode: %s", player_status, current_mode)
        
        if player_status in ['play', 'loading']:
            await self._update_media_info(status)
            self._handle_state_update(States.PLAYING)
        elif player_status == 'pause':
            await self._update_media_info(status)
            self._handle_state_update(States.PAUSED)
        elif player_status == 'stop':
            self._clear_all_media_info()
            self._handle_state_update(States.STANDBY)
        else:
            self._clear_all_media_info()
            self._handle_state_update(States.STANDBY)

    def _should_force_metadata_clear(self, current_mode: int, current_status: str) -> bool:
        """Determine if we should force clear metadata based on source characteristics."""
        # Spotify Connect mode
        spotify_mode = 31
        
        # Network/radio modes that typically have minimal metadata
        radio_modes = [10, 11, 16]  # Network modes
        
        # Force clear when switching FROM Spotify TO radio/network modes
        if (self._last_mode == spotify_mode and 
            current_mode in radio_modes and 
            current_status in ['play', 'loading']):
            _LOG.info("🎯 FORCE CLEAR: Spotify → Radio/Network transition detected")
            return True
            
        # Force clear when going from any mode with meaningful metadata to stop
        if (self._last_meaningful_metadata and 
            current_status == 'stop' and 
            self._last_status in ['play', 'pause']):
            _LOG.info("🎯 FORCE CLEAR: Playback stopped, clearing stale metadata")
            return True
            
        return False

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

    def _clear_all_media_info(self):
        """Clear ALL media information attributes."""
        media_attrs = [
            Attributes.MEDIA_TITLE, Attributes.MEDIA_ARTIST, Attributes.MEDIA_ALBUM,
            Attributes.MEDIA_IMAGE_URL, Attributes.MEDIA_DURATION, 
            Attributes.MEDIA_POSITION, Attributes.MEDIA_TYPE
        ]
        
        # Track what we're clearing for debugging
        cleared_attrs = []
        for attr in media_attrs:
            if attr in self.attributes:
                cleared_attrs.append(attr.value)
                self.attributes.pop(attr, None)
        
        if cleared_attrs:
            _LOG.info("🧹 CLEARED ATTRIBUTES: %s", cleared_attrs)
        
        # Clear our tracking of meaningful metadata
        self._last_meaningful_metadata.clear()

    async def _update_media_info(self, player_status: dict):
        """Update media information from metadata."""
        try:
            metadata = await self._client.get_track_metadata()
            
            if not metadata:
                _LOG.debug("No metadata available from device")
                return
                
            # Check if this is meaningful metadata or just placeholders
            if self._has_meaningful_metadata(metadata):
                _LOG.debug("📋 Processing meaningful metadata")
                self._set_media_metadata(metadata)
                self._set_position_duration(player_status)
                self._set_media_type(player_status)
                
                # Store meaningful metadata for clearing logic
                self._last_meaningful_metadata = metadata.copy()
            else:
                _LOG.debug("📋 Placeholder metadata detected, not setting attributes")
                # For placeholder metadata (radio stations), only set title if it's not a placeholder
                title = self._clean_metadata(metadata.get('title'))
                if title:
                    self.attributes[Attributes.MEDIA_TITLE] = title
                    _LOG.debug("Set radio title: %s", title)
                    
                # Set image URL if available for radio
                if image_url := self._clean_metadata(metadata.get('albumArtURI')):
                    self.attributes[Attributes.MEDIA_IMAGE_URL] = image_url
                    _LOG.debug("Set radio image: %s", image_url)
                
                # Set media type for radio
                self._set_media_type(player_status)
                
        except Exception as e:
            _LOG.error("Error updating media info: %s", e)
            self._clear_all_media_info()

    def _has_meaningful_metadata(self, metadata: dict) -> bool:
        """Check if metadata contains meaningful information (not placeholders)."""
        if not metadata:
            return False
            
        # Check for non-placeholder values in key fields
        meaningful_fields = ['title', 'artist', 'album']
        for field in meaningful_fields:
            if self._clean_metadata(metadata.get(field)):
                # If we have at least title OR (artist and album), consider it meaningful
                if field == 'title':
                    return True
                elif field in ['artist', 'album']:
                    # Need both artist and album to be meaningful
                    artist = self._clean_metadata(metadata.get('artist'))
                    album = self._clean_metadata(metadata.get('album'))
                    if artist and album:
                        return True
        return False

    def _set_media_metadata(self, metadata: dict):
        """Set media metadata attributes - only for valid values."""
        if title := self._clean_metadata(metadata.get('title')):
            self.attributes[Attributes.MEDIA_TITLE] = title
            _LOG.debug("Set media title: %s", title)
            
        if artist := self._clean_metadata(metadata.get('artist')):
            self.attributes[Attributes.MEDIA_ARTIST] = artist
            _LOG.debug("Set media artist: %s", artist)
            
        if album := self._clean_metadata(metadata.get('album')):
            self.attributes[Attributes.MEDIA_ALBUM] = album
            _LOG.debug("Set media album: %s", album)
            
        if image_url := self._clean_metadata(metadata.get('albumArtURI')):
            self.attributes[Attributes.MEDIA_IMAGE_URL] = image_url
            _LOG.debug("Set media image URL: %s", image_url)

    def _set_position_duration(self, player_status: dict):
        """Set position and duration attributes - only for tracks with duration."""
        # Get duration first to determine if this is a track or stream
        duration = 0
        if 'totlen' in player_status:
            duration = int(player_status['totlen']) // 1000
            
        # Only set duration and position for actual tracks (duration > 0)
        # Radio streams and live content should not have seek functionality
        if duration > 0:
            self.attributes[Attributes.MEDIA_DURATION] = duration
            _LOG.debug("Set media duration: %s seconds", duration)
            
            if 'curpos' in player_status:
                position = int(player_status['curpos']) // 1000
                self.attributes[Attributes.MEDIA_POSITION] = position
                _LOG.debug("Set media position: %s seconds", position)
        else:
            # For radio/streaming: explicitly ensure no duration or position
            _LOG.debug("Radio/stream detected (duration=0), not setting position/duration")

    def _set_media_type(self, player_status: dict):
        """Set media type based on mode."""
        mode = int(player_status.get('mode', 0))
        if mode in [31, 32, 10, 11, 16]:  # Music streaming modes
            self.attributes[Attributes.MEDIA_TYPE] = MediaType.MUSIC

    def _clean_metadata(self, value: Optional[str]) -> Optional[str]:
        """Clean metadata values - filter out WiiM's placeholder values."""
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
                _LOG.info("Switching to source/function: %s", source)
                
                # Set flag to clear metadata on next update for regular sources
                if source not in ['display_on', 'display_off', 'toggle_display', 'reboot_device']:
                    self._metadata_clear_pending = True
                    _LOG.info("🧹 METADATA CLEAR PENDING: Source switch to %s", source)
                
                # Handle different types of source/function switching
                if source in ['display_on', 'display_off', 'toggle_display', 'reboot_device']:
                    await self._handle_device_function(source)
                else:
                    await self._client.send_command(f"setPlayerCmd:switchmode:{source}")
                
                # Force immediate state update for regular source changes only
                if source not in ['display_on', 'display_off', 'toggle_display', 'reboot_device']:
                    asyncio.create_task(self._immediate_update_after_source_change())
            else:
                _LOG.warning("Unhandled command: %s", cmd_id)
                return StatusCodes.NOT_IMPLEMENTED
            
            # Only defer update for non-special commands
            if not (cmd_id == Commands.SELECT_SOURCE and params.get('source') in 
                   ['display_on', 'display_off', 'toggle_display', 'reboot_device']):
                asyncio.create_task(self._deferred_update())
                
            return StatusCodes.OK
            
        except Exception as e:
            _LOG.error("Error handling command %s: %s", cmd_id, e)
            return StatusCodes.SERVER_ERROR

    async def _handle_device_function(self, function: str):
        """Handle WiiM device special functions."""
        try:
            function_commands = {
                'display_on': 'setLightOperationBrightConfig:{"disable":0}',
                'display_off': 'setLightOperationBrightConfig:{"disable":1}',
                'toggle_display': None,
                'reboot_device': 'reboot'
            }
            
            if function == 'toggle_display':
                command = 'setLightOperationBrightConfig:{"disable":1}'
                _LOG.info("Toggle display - defaulting to display off")
            else:
                command = function_commands.get(function)
            
            if command:
                _LOG.info("Executing device function command: %s", command)
                await self._client.send_command(command)
                
                if function == 'reboot_device':
                    _LOG.warning("Device reboot command sent")
            else:
                _LOG.warning("Unknown device function: %s", function)
                
        except Exception as e:
            _LOG.error("Error executing device function %s: %s", function, e)

    async def _immediate_update_after_source_change(self):
        """Immediate update after source change to clear stale metadata faster."""
        await asyncio.sleep(0.5)
        await self.update_attributes()

    async def _deferred_update(self):
        """Update attributes after a short delay."""
        await asyncio.sleep(1.0)
        await self.update_attributes()