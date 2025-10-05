"""
WiiM Remote Entity Implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MIT, see LICENSE for more details.
"""

import logging
from typing import Any, Dict, List

from ucapi import StatusCodes
from ucapi.remote import Attributes, Features, Remote, States
from ucapi.ui import Buttons, create_btn_mapping

_LOG = logging.getLogger(__name__)

class WiiMRemote(Remote):
    """WiiM Remote entity with dynamic UI generation and physical button mapping."""

    def __init__(self, device_id: str, device_name: str):
        """Initialize remote entity."""
        features = [Features.SEND_CMD, Features.ON_OFF, Features.TOGGLE]
        attributes = {Attributes.STATE: States.ON}
        
        simple_commands = self._build_base_commands()
        button_mapping = self._create_button_mapping()
        ui_pages = [self._create_main_page()]
        
        super().__init__(
            identifier=f"{device_id}_remote",
            name=f"{device_name} Remote",
            features=features,
            attributes=attributes,
            simple_commands=simple_commands,
            button_mapping=button_mapping,
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
        commands = [
            # Playback controls
            'play', 'pause', 'stop', 'next', 'previous',
            'volume_up', 'volume_down', 'mute_toggle', 'mute_on', 'mute_off',
            # Device controls
            'display_on', 'display_off', 'toggle_display', 'reboot_device',
            # Input sources (standard)
            'wifi', 'bluetooth', 'line-in', 'optical', 'HDMI', 'phono', 'udisk',
            # Audio output query
            'output_get_current',
            # Remote navigation
            'dpad_up', 'dpad_down', 'dpad_left', 'dpad_right', 'dpad_select',
            'back', 'home',
        ]
        return commands

    def _create_button_mapping(self) -> List:
        """Create physical button to command mappings for Remote Two/3."""
        mappings = [
            # Transport controls
            create_btn_mapping(Buttons.PLAY, short="play"),
            create_btn_mapping(Buttons.PREV, short="previous"),
            create_btn_mapping(Buttons.NEXT, short="next"),
            
            # Volume controls
            create_btn_mapping(Buttons.VOLUME_UP, short="volume_up"),
            create_btn_mapping(Buttons.VOLUME_DOWN, short="volume_down"),
            create_btn_mapping(Buttons.MUTE, short="mute_toggle"),
            
            # D-Pad navigation
            create_btn_mapping(Buttons.DPAD_UP, short="dpad_up"),
            create_btn_mapping(Buttons.DPAD_DOWN, short="dpad_down"),
            create_btn_mapping(Buttons.DPAD_LEFT, short="dpad_left"),
            create_btn_mapping(Buttons.DPAD_RIGHT, short="dpad_right"),
            create_btn_mapping(Buttons.DPAD_MIDDLE, short="dpad_select"),
            
            # Navigation
            create_btn_mapping(Buttons.BACK, short="back"),
            create_btn_mapping(Buttons.HOME, short="home"),
            
            # Power - long press for reboot
            create_btn_mapping(Buttons.POWER, short="stop", long="reboot_device"),
            
            # Color buttons for quick source switching (will be overridden with services if available)
            create_btn_mapping(Buttons.RED, short="wifi"),
            create_btn_mapping(Buttons.GREEN, short="bluetooth"),
            create_btn_mapping(Buttons.YELLOW, short="line-in"),
            create_btn_mapping(Buttons.BLUE, short="optical"),
        ]
        
        return mappings

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
                
                # Display controls + Main sources
                {'type': 'text', 'location': {'x': 0, 'y': 2}, 'text': 'DISP OFF', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'display_off'}}},
                {'type': 'text', 'location': {'x': 1, 'y': 2}, 'text': 'WiFi', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'wifi'}}},
                {'type': 'text', 'location': {'x': 2, 'y': 2}, 'text': 'BT', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'bluetooth'}}},
                {'type': 'text', 'location': {'x': 3, 'y': 2}, 'text': 'Line', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'line-in'}}},
                
                # Additional sources + display on
                {'type': 'text', 'location': {'x': 0, 'y': 3}, 'text': 'DISP ON', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'display_on'}}},
                {'type': 'text', 'location': {'x': 1, 'y': 3}, 'text': 'HDMI', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'HDMI'}}},
                {'type': 'text', 'location': {'x': 2, 'y': 3}, 'text': 'USB', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'udisk'}}},
                {'type': 'text', 'location': {'x': 3, 'y': 3}, 'text': 'Optical', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'optical'}}},
            ]
        }

    async def initialize_capabilities(self):
        """Initialize capabilities and create dynamic UI pages."""
        if self._capabilities_initialized or not self._client:
            return
        
        # Build extended commands including discovered capabilities
        extended_commands = self._build_extended_commands()
        
        # Create dynamic UI pages
        all_pages = self._create_dynamic_pages()
        
        # Update button mappings with discovered sources
        extended_button_mapping = self._create_extended_button_mapping()
        
        # Update options
        self.options = {
            'simple_commands': extended_commands,
            'button_mapping': extended_button_mapping,
            'user_interface': {'pages': all_pages}
        }
        
        self.attributes[Attributes.STATE] = States.ON
        self._force_integration_update()
        
        self._capabilities_initialized = True
        _LOG.info("Remote initialized with %d commands, %d button mappings, and %d pages", 
                 len(extended_commands), len(extended_button_mapping), len(all_pages))

    def _build_extended_commands(self) -> List[str]:
        """Build extended command list based on discovered capabilities."""
        commands = self._build_base_commands()
        
        # Add discovered input sources
        if self._client.sources:
            commands.extend(self._client.sources.keys())
            
        # Add discovered audio outputs (DYNAMIC)
        if self._client.audio_outputs:
            commands.extend(self._client.audio_outputs.keys())
            _LOG.info("Added %d audio output commands to remote", len(self._client.audio_outputs))
            
            # Add combo commands for discovered outputs
            combo_commands = []
            for input_source in ['wifi', 'bluetooth', 'line', 'hdmi', 'optical']:
                for output_cmd in self._client.audio_outputs.keys():
                    output_name = output_cmd.replace('output_', '')
                    combo_commands.append(f"combo_{input_source}_{output_name}")
            commands.extend(combo_commands)
            
        # Add EQ presets
        if self._client.eq_presets:
            eq_commands = [f"eq_{p.lower().replace(' ', '_').replace('-', '_')}" 
                          for p in self._client.eq_presets]
            commands.extend(eq_commands + ['eq_on', 'eq_off'])
            
        # Add user presets
        if self._client.presets:
            preset_commands = [f"preset_{p['number']}" for p in self._client.presets]
            commands.extend(preset_commands)
            
            # Add service-specific commands for discovered music services
            services_found = set()
            for preset in self._client.presets:
                source = preset.get('source', '').lower()
                # Create normalized service command
                if source and source not in services_found:
                    service_cmd = f"service_{source.replace(' ', '_').lower()}"
                    commands.append(service_cmd)
                    services_found.add(source)
                    _LOG.info("Added music service command: %s", service_cmd)
            
        return commands

    def _create_extended_button_mapping(self) -> List[dict]:
        """Create extended button mappings including music services on color buttons."""
        # Start with base mappings - convert to dicts
        mappings = []
        for mapping in self._create_button_mapping():
            if hasattr(mapping, '__dict__'):
                # Convert dataclass to dict
                mapping_dict = {
                    'button': mapping.button,
                    'short_press': None,
                    'long_press': None
                }
                if mapping.short_press:
                    mapping_dict['short_press'] = {
                        'cmd_id': mapping.short_press.cmd_id,
                        'params': mapping.short_press.params
                    }
                if mapping.long_press:
                    mapping_dict['long_press'] = {
                        'cmd_id': mapping.long_press.cmd_id,
                        'params': mapping.long_press.params
                    }
                mappings.append(mapping_dict)
            else:
                mappings.append(mapping)
        
        # Override color buttons with top 4 music services if available
        if self._client and self._client.presets:
            services_by_source = {}
            for preset in self._client.presets:
                source = preset.get('source', 'Unknown')
                if source not in services_by_source:
                    services_by_source[source] = []
                services_by_source[source].append(preset)
            
            service_list = list(services_by_source.keys())[:4]  # Top 4 services
            color_buttons = ['RED', 'GREEN', 'YELLOW', 'BLUE']
            
            # Remove old color button mappings
            mappings = [m for m in mappings if m.get('button') not in color_buttons]
            
            # Add new service mappings
            for i, service_name in enumerate(service_list):
                if i >= len(color_buttons):
                    break
                service_cmd = f"service_{service_name.replace(' ', '_').lower()}"
                mappings.append({
                    'button': color_buttons[i],
                    'short_press': {'cmd_id': 'send_cmd', 'params': {'command': service_cmd}},
                    'long_press': None
                })
                _LOG.info("Mapped %s button to service: %s", color_buttons[i], service_name)
        
        # Add channel up/down for preset navigation if presets exist
        if self._client and self._client.presets:
            if len(self._client.presets) >= 1:
                mappings.append({
                    'button': 'CHANNEL_UP',
                    'short_press': {'cmd_id': 'send_cmd', 'params': {'command': f'preset_{self._client.presets[0]["number"]}'}},
                    'long_press': None
                })
            if len(self._client.presets) >= 2:
                mappings.append({
                    'button': 'CHANNEL_DOWN',
                    'short_press': {'cmd_id': 'send_cmd', 'params': {'command': f'preset_{self._client.presets[1]["number"]}'}},
                    'long_press': None
                })
        
        return mappings

    def _create_dynamic_pages(self) -> List[Dict[str, Any]]:
        """Create all UI pages based on device capabilities."""
        pages = [self._create_main_page()]
        
        # Add music services page
        if self._client.presets:
            if services_page := self._create_services_page():
                pages.append(services_page)
            if presets_page := self._create_presets_page():
                pages.append(presets_page)
        
        # Add audio output control page
        if self._client.audio_outputs and (audio_page := self._create_audio_output_page()):
            pages.append(audio_page)
        
        # Add EQ page
        if self._client.eq_presets:
            if eq_page := self._create_eq_page():
                pages.append(eq_page)
                
        # Add device control page
        if device_page := self._create_device_control_page():
            pages.append(device_page)
        
        return pages

    def _create_services_page(self) -> Dict[str, Any]:
        """Create music services page based on preset sources."""
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
            
            # Use service command
            service_cmd = f"service_{source_name.replace(' ', '_').lower()}"
            service_label = source_name[:10]
            
            page['items'].append({
                'type': 'text',
                'location': {'x': col, 'y': row},
                'text': service_label,
                'command': {'cmd_id': 'send_cmd', 'params': {'command': service_cmd}}
            })
            
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        return page if page['items'] else None

    def _create_presets_page(self) -> Dict[str, Any]:
        """Create presets page - shows all configured presets."""
        page = {
            'page_id': 'presets',
            'name': 'Presets',
            'grid': {'width': 4, 'height': 6},
            'items': []
        }
        
        row, col = 0, 0
        for preset in self._client.presets[:12]:  # Max 12 presets
            num = preset['number']
            name = preset['name'][:8]
            
            page['items'].append({
                'type': 'text',
                'location': {'x': col, 'y': row},
                'text': f"#{num}",
                'command': {'cmd_id': 'send_cmd', 'params': {'command': f'preset_{num}'}}
            })
            
            # Add preset name below number (if space)
            if row + 1 < 6:
                page['items'].append({
                    'type': 'text',
                    'location': {'x': col, 'y': row + 1},
                    'text': name,
                    'command': {'cmd_id': 'send_cmd', 'params': {'command': f'preset_{num}'}}
                })
            
            col += 1
            if col >= 4:
                col = 0
                row += 2  # Skip row for names
            if row >= 6:
                break
        
        return page if page['items'] else None

    def _create_audio_output_page(self) -> Dict[str, Any]:
        """Create audio output control page based on discovered outputs."""
        if not self._client.audio_outputs:
            return None
            
        page = {
            'page_id': 'audio_output',
            'name': 'Audio Output',
            'grid': {'width': 4, 'height': 6},
            'items': []
        }
        
        # Add individual output controls dynamically
        row, col = 0, 0
        for output_cmd, output_name in self._client.audio_outputs.items():
            if row >= 2:  # Limit to first 2 rows for individual controls
                break
                
            label = output_name[:10]  # Truncate for UI
            page['items'].append({
                'type': 'text',
                'location': {'x': col, 'y': row},
                'text': label,
                'command': {'cmd_id': 'send_cmd', 'params': {'command': output_cmd}}
            })
            
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        # Add get current output mode button
        page['items'].append({
            'type': 'text',
            'location': {'x': 3, 'y': 0},
            'text': 'Get Mode',
            'command': {'cmd_id': 'send_cmd', 'params': {'command': 'output_get_current'}}
        })
        
        # Add combo commands for activities (remaining rows)
        combo_row = 2
        combo_col = 0
        combo_count = 0
        
        for input_source in ['wifi', 'bluetooth', 'line', 'hdmi']:
            for output_cmd, output_name in list(self._client.audio_outputs.items())[:2]:  # Limit combos
                if combo_row >= 6 or combo_count >= 8:  # Limit total combo buttons
                    break
                    
                output_short = output_cmd.replace('output_', '')[:4]
                input_short = input_source[:4] if input_source != 'bluetooth' else 'BT'
                label = f"{input_short}→{output_short}"
                
                combo_command = f"combo_{input_source}_{output_cmd.replace('output_', '')}"
                
                page['items'].append({
                    'type': 'text',
                    'location': {'x': combo_col, 'y': combo_row},
                    'text': label,
                    'command': {'cmd_id': 'send_cmd', 'params': {'command': combo_command}}
                })
                
                combo_col += 1
                combo_count += 1
                if combo_col >= 4:
                    combo_col = 0
                    combo_row += 1
        
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

    def _create_device_control_page(self) -> Dict[str, Any]:
        """Create device control page for display and system functions."""
        return {
            'page_id': 'device',
            'name': 'Device Control',
            'grid': {'width': 4, 'height': 6},
            'items': [
                # Display controls
                {'type': 'text', 'location': {'x': 0, 'y': 0}, 'text': 'Display On', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'display_on'}}},
                {'type': 'text', 'location': {'x': 1, 'y': 0}, 'text': 'Display Off', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'display_off'}}},
                {'type': 'text', 'location': {'x': 2, 'y': 0}, 'text': 'Toggle Disp', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'toggle_display'}}},
                
                # System control
                {'type': 'text', 'location': {'x': 0, 'y': 1}, 'text': 'REBOOT', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'reboot_device'}}},
                
                # Quick access buttons
                {'type': 'text', 'location': {'x': 2, 'y': 1}, 'text': 'WiFi Mode', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'wifi'}}},
                {'type': 'text', 'location': {'x': 3, 'y': 1}, 'text': 'BT Mode', 
                 'command': {'cmd_id': 'send_cmd', 'params': {'command': 'bluetooth'}}},
            ]
        }

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
            if cmd_id == "send_cmd" and params and 'command' in params:
                command = params['command']
                await self._execute_command(command)
            elif cmd_id == "on":
                self.attributes[Attributes.STATE] = States.ON
                self._force_integration_update()
            elif cmd_id == "off":
                self.attributes[Attributes.STATE] = States.OFF
                await self._client.stop_playback()
                self._force_integration_update()
            elif cmd_id == "toggle":
                new_state = States.OFF if self.attributes[Attributes.STATE] == States.ON else States.ON
                self.attributes[Attributes.STATE] = new_state
                if new_state == States.OFF:
                    await self._client.stop_playback()
                self._force_integration_update()
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
            'mute_on': lambda: self._client.set_mute(True),
            'mute_off': lambda: self._client.set_mute(False),
        }
        
        if command in basic_commands:
            await basic_commands[command]()
            return
        
        # D-Pad navigation (map to playback for now)
        dpad_commands = {
            'dpad_up': self._client.volume_up,
            'dpad_down': self._client.volume_down,
            'dpad_left': self._client.previous_track,
            'dpad_right': self._client.next_track,
            'dpad_select': self._client.toggle_playback,
            'back': self._client.stop_playback,
            'home': self._client.stop_playback,
        }
        
        if command in dpad_commands:
            await dpad_commands[command]()
            return
        
        # Display and device control commands
        if command == 'display_on':
            await self._client.send_command('setLightOperationBrightConfig:{"disable":0}')
        elif command == 'display_off':
            await self._client.send_command('setLightOperationBrightConfig:{"disable":1}')
        elif command == 'toggle_display':
            await self._client.send_command('setLightOperationBrightConfig:{"disable":1}')
        elif command == 'reboot_device':
            _LOG.warning("Reboot command executed - device will be unavailable during restart")
            await self._client.send_command('reboot')
        
        # Dynamic audio output control commands
        elif command.startswith('output_') and command != 'output_get_current':
            await self._execute_audio_output_command(command)
        elif command == 'output_get_current':
            result = await self._client.send_command('getNewAudioOutputHardwareMode')
            _LOG.info("Current audio output mode: %s", result)
            
        # Combo commands for activities (input + output)
        elif command.startswith('combo_'):
            await self._execute_combo_command(command)
        
        # Music service commands
        elif command.startswith('service_'):
            await self._execute_service_command(command)
        
        # Source switching
        elif command in ['wifi', 'bluetooth', 'line-in', 'optical', 'HDMI', 'phono', 'udisk']:
            await self._client.send_command(f"setPlayerCmd:switchmode:{command}")
        
        # EQ commands
        elif command == 'eq_on':
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

    async def _execute_service_command(self, command: str):
        """Execute music service command - activates first preset of that service."""
        service_name = command.replace('service_', '').replace('_', ' ')
        
        # Find first preset matching this service
        for preset in self._client.presets:
            preset_source = preset.get('source', '').lower()
            if preset_source.replace(' ', '_') == service_name.replace(' ', '_'):
                preset_num = preset['number']
                _LOG.info("Activating %s via preset #%d (%s)", service_name, preset_num, preset.get('name', 'Unknown'))
                await self._client.send_command(f"MCUKeyShortClick:{preset_num}")
                return
        
        _LOG.warning("No preset found for service: %s", service_name)

    async def _execute_audio_output_command(self, command: str):
        """Execute audio output control command dynamically."""
        output_mode_map = {
            'output_spdif': '1',
            'output_aux_line_out': '2', 
            'output_coax': '3'
        }
        
        # Get the mode number for this command
        mode_num = output_mode_map.get(command)
        if mode_num:
            await self._client.send_command(f"setAudioOutputHardwareMode:{mode_num}")
            output_name = self._client.audio_outputs.get(command, command)
            _LOG.info("Audio output set to: %s (mode %s)", output_name, mode_num)
        else:
            _LOG.warning("Unknown audio output command: %s", command)

    async def _execute_combo_command(self, command: str):
        """Execute combination input/output commands for activities."""
        # Parse combo command format: combo_{input}_{output}
        parts = command.split('_', 2)  # Split into max 3 parts
        if len(parts) >= 3:
            input_source = parts[1]
            output_part = parts[2]
            
            # Map output parts to hardware mode numbers
            output_map = {
                'spdif': '1',
                'aux': '2',
                'line': '2',  # aux/line out is same mode
                'coax': '3'
            }
            
            # Handle compound output names (e.g., aux_line_out)
            mode_num = None
            for key, value in output_map.items():
                if key in output_part:
                    mode_num = value
                    break
            
            # Execute input source switch first
            if input_source in ['wifi', 'bluetooth', 'line', 'hdmi', 'optical', 'phono', 'udisk']:
                source_command = input_source if input_source != 'line' else 'line-in'
                await self._client.send_command(f"setPlayerCmd:switchmode:{source_command}")
                _LOG.info("Switched input to: %s", source_command)
                
                # Small delay to allow input switch to complete
                import asyncio
                await asyncio.sleep(0.5)
            
            # Execute output mode switch
            if mode_num:
                await self._client.send_command(f"setAudioOutputHardwareMode:{mode_num}")
                _LOG.info("Switched output to mode %s (%s)", mode_num, output_part)
            else:
                _LOG.warning("Could not determine output mode for: %s", output_part)