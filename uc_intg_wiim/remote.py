"""
WiiM Remote Entity Implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MIT, see LICENSE for more details.
"""

import logging
from typing import Any, Dict, List

from ucapi import StatusCodes
from ucapi.remote import Attributes, Features, Remote, States

_LOG = logging.getLogger(__name__)

class WiiMRemote(Remote):
    """WiiM Remote entity with dynamic UI generation."""

    def __init__(self, device_id: str, device_name: str):
        """Initialize remote entity."""
        features = [Features.ON_OFF, Features.SEND_CMD]
        attributes = {Attributes.STATE: States.ON}
        
        simple_commands = self._build_base_commands()
        ui_pages = [self._create_main_page()]
        
        super().__init__(
            identifier=f"{device_id}_remote",
            name=f"{device_name} Remote",
            features=features,
            attributes=attributes,
            simple_commands=simple_commands,
            ui_pages=ui_pages,
            cmd_handler=self._handle_command,
        )
        
        self._client = None
        self._integration_api = None
        self._capabilities_initialized = False

    def set_client(self, client):
        """Set the WiiM client."""
        self._client = client

    def _build_base_commands(self) -> List[str]:
        """Build base command list."""
        return [
            'play', 'pause', 'stop', 'next', 'previous',
            'volume_up', 'volume_down', 'mute_toggle', 'on', 'off',
            'wifi', 'bluetooth', 'line-in', 'optical', 'HDMI', 'phono', 'udisk'
        ]

    def _create_main_page(self) -> Dict[str, Any]:
        """Create main control page."""
        return {
            'page_id': 'main',
            'name': 'Main Controls',
            'grid': {'width': 4, 'height': 6},
            'items': [
                # Transport controls
                {'type': 'text', 'location': {'x': 0, 'y': 0}, 'text': 'PREV', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'previous'}}},
                {'type': 'text', 'location': {'x': 1, 'y': 0}, 'text': 'PLAY', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'play'}}},
                {'type': 'text', 'location': {'x': 2, 'y': 0}, 'text': 'PAUSE', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'pause'}}},
                {'type': 'text', 'location': {'x': 3, 'y': 0}, 'text': 'NEXT', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'next'}}},
                
                # Volume controls
                {'type': 'text', 'location': {'x': 0, 'y': 1}, 'text': 'VOL-', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'volume_down'}}},
                {'type': 'text', 'location': {'x': 1, 'y': 1}, 'text': 'VOL+', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'volume_up'}}},
                {'type': 'text', 'location': {'x': 2, 'y': 1}, 'text': 'MUTE', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'mute_toggle'}}},
                {'type': 'text', 'location': {'x': 3, 'y': 1}, 'text': 'STOP', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'stop'}}},
                
                # Standby + Main sources (ON button removed)
                {'type': 'text', 'location': {'x': 0, 'y': 2}, 'text': 'STANDBY', 
                 'command': {'cmd_id': 'off', 'params': {}}},
                {'type': 'text', 'location': {'x': 1, 'y': 2}, 'text': 'WiFi', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'wifi'}}},
                {'type': 'text', 'location': {'x': 2, 'y': 2}, 'text': 'BT', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'bluetooth'}}},
                {'type': 'text', 'location': {'x': 3, 'y': 2}, 'text': 'Line', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'line-in'}}},
                
                # Additional sources (adjusted layout after removing ON button)
                {'type': 'text', 'location': {'x': 0, 'y': 3}, 'text': 'Optical', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'optical'}}},
                {'type': 'text', 'location': {'x': 1, 'y': 3}, 'text': 'HDMI', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'HDMI'}}},
                {'type': 'text', 'location': {'x': 2, 'y': 3}, 'text': 'USB', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'udisk'}}},
                {'type': 'text', 'location': {'x': 3, 'y': 3}, 'text': 'Phono', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'phono'}}},
            ]
        }

    async def initialize_capabilities(self):
        """Initialize capabilities and create dynamic UI pages."""
        if self._capabilities_initialized or not self._client:
            return
        
        extended_commands = self._build_extended_commands()
        all_pages = self._create_dynamic_pages()
        
        self.options = {
            'simple_commands': extended_commands,
            'user_interface': {'pages': all_pages}
        }
        
        self.attributes[Attributes.STATE] = States.ON
        self._force_integration_update()
        
        self._capabilities_initialized = True
        _LOG.info("Remote initialized with %d commands and %d pages", 
                 len(extended_commands), len(all_pages))

    def _build_extended_commands(self) -> List[str]:
        """Build extended command list based on discovered capabilities."""
        commands = self._build_base_commands()
        
        if self._client.sources:
            commands.extend(self._client.sources.keys())
            
        if self._client.eq_presets:
            eq_commands = [f"eq_{p.lower().replace(' ', '_').replace('-', '_')}" 
                          for p in self._client.eq_presets]
            commands.extend(eq_commands + ['eq_on', 'eq_off'])
            
        if self._client.presets:
            preset_commands = [f"preset_{p['number']}" for p in self._client.presets]
            commands.extend(preset_commands)
            
        return commands

    def _create_dynamic_pages(self) -> List[Dict[str, Any]]:
        """Create all UI pages based on device capabilities."""
        pages = [self._create_main_page()]
        
        if self._client.presets:
            if services_page := self._create_services_page():
                pages.append(services_page)
            if presets_page := self._create_presets_page():
                pages.append(presets_page)
        
        if self._client.eq_presets:
            if eq_page := self._create_eq_page():
                pages.append(eq_page)
        
        return pages

    def _create_services_page(self) -> Dict[str, Any]:
        """Create services page based on preset sources."""
        services_by_source = {}
        for preset in self._client.presets:
            source = preset.get('source', 'Unknown')
            if source not in services_by_source:
                services_by_source[source] = []
            services_by_source[source].append(preset)
        
        if not services_by_source:
            return None
            
        page = {
            'page_id': 'services',
            'name': 'Music Services',
            'grid': {'width': 4, 'height': 6},
            'items': []
        }
        
        row, col = 0, 0
        for source_name, presets_list in services_by_source.items():
            if row >= 6:
                break
                
            service_label = source_name[:10]
            page['items'].append({
                'type': 'text',
                'location': {'x': col, 'y': row},
                'text': service_label,
                'command': {'cmd_id': 'send_cmd', 'params': {'command': f'preset_{presets_list[0]["number"]}'}}
            })
            
            if len(presets_list) > 1:
                count_text = f"({len(presets_list)})"
                page['items'].append({
                    'type': 'text',
                    'location': {'x': col, 'y': row + 1},
                    'text': count_text,
                    'command': {'cmd_id': 'send_cmd', 'params': {'command': f'preset_{presets_list[0]["number"]}'}}
                })
                row += 2
            else:
                row += 1
            
            col += 1
            if col >= 4:
                col = 0
                if row < 6:
                    row += 1
        
        return page if page['items'] else None

    def _create_presets_page(self) -> Dict[str, Any]:
        """Create presets page."""
        page = {
            'page_id': 'presets',
            'name': 'Presets',
            'grid': {'width': 4, 'height': 6},
            'items': []
        }
        
        row, col = 0, 0
        for preset in self._client.presets[:12]:
            num = preset['number']
            name = preset['name'][:8]
            
            page['items'].extend([
                {'type': 'text', 'location': {'x': col, 'y': row}, 'text': f"#{num}", 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': f'preset_{num}'}}},
                {'type': 'text', 'location': {'x': col, 'y': row + 1}, 'text': name, 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': f'preset_{num}'}}}
            ])
            
            col += 1
            if col >= 4:
                col = 0
                row += 2
            if row >= 6:
                break
        
        return page if page['items'] else None

    def _create_eq_page(self) -> Dict[str, Any]:
        """Create equalizer page."""
        page = {
            'page_id': 'equalizer',
            'name': 'Equalizer',
            'grid': {'width': 4, 'height': 6},
            'items': [
                {'type': 'text', 'location': {'x': 0, 'y': 0}, 'text': 'EQ On', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'eq_on'}}},
                {'type': 'text', 'location': {'x': 1, 'y': 0}, 'text': 'EQ Off', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'eq_off'}}},
            ]
        }
        
        row, col = 1, 0
        for preset in self._client.eq_presets[:14]:
            cmd = f"eq_{preset.lower().replace(' ', '_').replace('-', '_')}"
            label = preset[:8]
            
            page['items'].append({
                'type': 'text',
                'location': {'x': col, 'y': row},
                'text': label,
                'command': {'cmd_id': 'send_cmd', 'params': {'command': cmd}}
            })
            
            col += 1
            if col >= 4:
                col = 0
                row += 1
            if row >= 6:
                break
        
        return page

    async def update_attributes(self):
        """Update remote attributes."""
        if not self._capabilities_initialized:
            await self.initialize_capabilities()
        
        self.attributes[Attributes.STATE] = States.ON
        self._force_integration_update()

    def _force_integration_update(self):
        """Force update to integration API."""
        if self._integration_api:
            try:
                self._integration_api.configured_entities.update_attributes(
                    self.id, {Attributes.STATE: States.ON}
                )
            except:
                pass

    async def _handle_command(self, entity, cmd_id: str, params: dict = None) -> StatusCodes:
        """Handle remote commands."""
        if not self._client:
            return StatusCodes.SERVER_ERROR
            
        try:
            if cmd_id == "off":
                _LOG.info("STANDBY command - stopping playback")
                await self._client.stop_playback()
                
            elif cmd_id == "send_cmd" and params and 'command' in params:
                command = params['command']
                await self._execute_command(command)
                
            else:
                return StatusCodes.NOT_IMPLEMENTED
                
            return StatusCodes.OK
            
        except Exception as e:
            _LOG.error("Error executing command: %s", e)
            return StatusCodes.SERVER_ERROR

    async def _execute_command(self, command: str):
        """Execute specific command."""
        # Basic playback commands
        basic_commands = {
            'play': self._client.resume_playback,
            'pause': self._client.pause_playback,
            'stop': self._client.stop_playback,
            'next': self._client.next_track,
            'previous': self._client.previous_track,
            'volume_up': self._client.volume_up,
            'volume_down': self._client.volume_down,
            'mute_toggle': self._client.toggle_mute,
        }
        
        if command in basic_commands:
            await basic_commands[command]()
            return
        
        # Source switching
        sources = ['wifi', 'bluetooth', 'line-in', 'optical', 'HDMI', 'phono', 'udisk']
        if command in sources:
            await self._client.send_command(f"setPlayerCmd:switchmode:{command}")
            return
        
        # EQ commands
        if command == 'eq_on':
            await self._client.send_command("EQOn")
        elif command == 'eq_off':
            await self._client.send_command("EQOff")
        elif command.startswith('eq_') and command not in ['eq_on', 'eq_off']:
            preset_name = command[3:].replace('_', ' ').title()
            await self._client.send_command(f"EQLoad:{preset_name}")
        
        # Preset commands
        elif command.startswith('preset_'):
            preset_num = command.split('_')[1]
            await self._client.send_command(f"MCUKeyShortClick:{preset_num}")
        
        else:
            _LOG.warning("Unhandled command: %s", command)