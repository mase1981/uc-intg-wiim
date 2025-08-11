#!/usr/bin/env python3
"""
WiiM Service Discovery Script
Standalone script to discover music services and browse capabilities.

Usage: python wiim_service_discovery.py
"""

import asyncio
import json
import aiohttp
import sys

class WiiMServiceDiscovery:
    def __init__(self, host: str):
        self.host = host
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_command(self, command: str):
        """Send command to WiiM device."""
        url = f"https://{self.host}/httpapi.asp?command={command}"
        try:
            async with self.session.get(url, timeout=5) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            return None
        return None

    async def explore_services(self):
        """Comprehensive service discovery."""
        print("=" * 60)
        print("WiiM SERVICE DISCOVERY TOOL")
        print("=" * 60)
        print(f"Testing device: {self.host}")
        
        # Test 1: Device Info Deep Dive
        print("\n🔍 1. DEVICE INFORMATION ANALYSIS")
        print("-" * 40)
        
        device_info_raw = await self.send_command("getStatusEx")
        if device_info_raw:
            try:
                device_info = json.loads(device_info_raw)
                print(f"✅ Device: {device_info.get('DeviceName', 'Unknown')}")
                print(f"✅ Firmware: {device_info.get('firmware', 'Unknown')}")
                
                # Look for service-related fields
                service_fields = []
                for key, value in device_info.items():
                    if any(word in key.lower() for word in ['service', 'stream', 'app', 'source', 'music', 'tidal', 'spotify']):
                        service_fields.append((key, value))
                        print(f"   🎵 {key}: {value}")
                
                if not service_fields:
                    print("   ℹ️  No obvious service fields found in device info")
                    
            except json.JSONDecodeError:
                print("   ❌ Could not parse device info JSON")
        else:
            print("   ❌ Could not get device info")

        # Test 2: Current Player Status
        print("\n🎮 2. CURRENT PLAYER STATUS")
        print("-" * 40)
        
        player_status_raw = await self.send_command("getPlayerStatus")
        if player_status_raw:
            try:
                player_status = json.loads(player_status_raw)
                mode = player_status.get('mode', 'unknown')
                status = player_status.get('status', 'unknown')
                
                print(f"   📊 Current Mode: {mode}")
                print(f"   📊 Status: {status}")
                
                # Decode mode based on API documentation
                mode_map = {
                    '0': 'None/Idle',
                    '1': 'AirPlay/AirPlay 2',
                    '2': '3rd party DLNA',
                    '10': 'Default WiiM mode',
                    '11': 'USB disk playlist',
                    '16': 'TF card playlist',
                    '31': 'Spotify Connect',
                    '32': 'TIDAL Connect',
                    '40': 'AUX-In',
                    '41': 'Bluetooth',
                    '42': 'External storage',
                    '43': 'Optical-In',
                    '50': 'Mirror',
                    '60': 'Voice mail',
                    '99': 'Slave'
                }
                
                service_name = mode_map.get(mode, f'Unknown mode {mode}')
                print(f"   🎵 Decoded Service: {service_name}")
                
            except json.JSONDecodeError:
                print("   ❌ Could not parse player status JSON")
        else:
            print("   ❌ Could not get player status")

        # Test 3: Browse/Service Endpoint Discovery
        print("\n🔍 3. TESTING POTENTIAL SERVICE ENDPOINTS")
        print("-" * 40)
        
        test_commands = [
            "getBrowseInfo",
            "getServiceList", 
            "getConfiguredServices",
            "getStreamingServices",
            "getSourceList",
            "browse",
            "services",
            "getPlaylist",
            "getLibrary",
            "getMusicServices",
            "getApps",
            "spotify_info",
            "tidal_info",
            "pandora_info",
            "amazon_info"
        ]
        
        found_endpoints = []
        for cmd in test_commands:
            result = await self.send_command(cmd)
            if result and result.strip() and result != "OK":
                found_endpoints.append((cmd, result))
                print(f"   ✅ {cmd}: {result[:100]}{'...' if len(result) > 100 else ''}")
        
        if not found_endpoints:
            print("   ℹ️  No additional service endpoints discovered")

        # Test 4: Metadata Analysis  
        print("\n🎶 4. CURRENT TRACK METADATA")
        print("-" * 40)
        
        metadata_raw = await self.send_command("getMetaInfo")
        if metadata_raw:
            try:
                metadata = json.loads(metadata_raw)
                if 'metaData' in metadata:
                    meta = metadata['metaData']
                    print(f"   🎵 Title: {meta.get('title', 'N/A')}")
                    print(f"   🎤 Artist: {meta.get('artist', 'N/A')}")
                    print(f"   💿 Album: {meta.get('album', 'N/A')}")
                    
                    # Check if there are service-specific fields
                    for key, value in meta.items():
                        if key not in ['title', 'artist', 'album', 'albumArtURI', 'sampleRate', 'bitDepth']:
                            print(f"   🔍 {key}: {value}")
                else:
                    print("   ℹ️  No metadata available")
            except json.JSONDecodeError:
                print("   ❌ Could not parse metadata JSON")
        else:
            print("   ❌ Could not get track metadata")

        # Test 5: Preset Analysis
        print("\n📻 5. PRESETS ANALYSIS (might contain services)")
        print("-" * 40)
        
        presets_raw = await self.send_command("getPresetInfo")
        if presets_raw:
            try:
                presets = json.loads(presets_raw)
                if 'preset_list' in presets:
                    print(f"   📊 Found {len(presets['preset_list'])} presets:")
                    for preset in presets['preset_list']:
                        source = preset.get('source', 'Unknown')
                        name = preset.get('name', 'Unnamed')
                        print(f"      #{preset.get('number', '?')}: {name} (Source: {source})")
                else:
                    print("   ℹ️  No presets found")
            except json.JSONDecodeError:
                print("   ❌ Could not parse presets JSON")
        else:
            print("   ❌ Could not get presets")

        # Test 6: Network Analysis
        print("\n🌐 6. NETWORK & CONNECTIVITY INFO")
        print("-" * 40)
        
        if device_info_raw:
            try:
                device_info = json.loads(device_info_raw)
                internet = device_info.get('internet', '0')
                print(f"   🌐 Internet Connected: {'Yes' if internet == '1' else 'No'}")
                print(f"   📡 WiFi Signal: {device_info.get('RSSI', 'Unknown')} dBm")
                
                # Check for streaming capabilities
                streams = device_info.get('streams', '0')
                streams_all = device_info.get('streams_all', '0')
                print(f"   🎵 Streams: {streams}")
                print(f"   🎵 All Streams: {streams_all}")
                
            except:
                pass

        print("\n" + "=" * 60)
        print("DISCOVERY COMPLETE!")
        print("=" * 60)
        
        if found_endpoints:
            print(f"\n✨ Found {len(found_endpoints)} potential service endpoints!")
            print("📋 Summary of discovered endpoints:")
            for cmd, result in found_endpoints:
                print(f"   • {cmd}")
        else:
            print("\n💡 RECOMMENDATIONS:")
            print("   • WiiM API may not expose configured services directly")
            print("   • Consider using mode switching to access services")
            print("   • Monitor mode changes when using official app")
            print("   • Services might be accessible via presets")

async def main():
    if len(sys.argv) != 2:
        print("Usage: python wiim_service_discovery.py <WIIM_IP_ADDRESS>")
        print("Example: python wiim_service_discovery.py 10.2.9.193")
        sys.exit(1)
    
    host = sys.argv[1]
    
    async with WiiMServiceDiscovery(host) as discovery:
        await discovery.explore_services()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Discovery cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")