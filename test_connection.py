#!/usr/bin/env python3
"""
WiiM Connection Test Script.

Usage: python test_connection.py <WIIM_IP_ADDRESS>
"""

import asyncio
import json
import sys
from typing import Optional

from uc_intg_wiim.client import WiiMClient


async def test_wiim_device(host: str) -> bool:
    """Test connection to WiiM device and display capabilities."""
    print(f"Testing connection to WiiM device at {host}...")
    
    try:
        async with WiiMClient(host) as client:
            # Test basic connection
            device_info = await client.get_device_info()
            if not device_info:
                print("❌ Failed to get device information")
                return False
            
            print("✅ Successfully connected to WiiM device!")
            print(f"   Device Name: {device_info.get('DeviceName', 'Unknown')}")
            print(f"   UUID: {device_info.get('uuid', 'Unknown')}")
            print(f"   Firmware: {device_info.get('firmware', 'Unknown')}")
            print(f"   Hardware: {device_info.get('hardware', 'Unknown')}")
            
            # Test player status
            player_status = await client.get_player_status()
            if player_status:
                print(f"   Current Status: {player_status.get('status', 'Unknown')}")
                print(f"   Volume: {player_status.get('vol', 'Unknown')}")
                print(f"   Mode: {player_status.get('mode', 'Unknown')}")
            
            # Discover capabilities
            await client.discover_capabilities()
            
            print(f"   Available Sources: {list(client.sources.keys())}")
            print(f"   EQ Presets: {len(client.eq_presets)} available")
            print(f"   User Presets: {len(client.presets)} configured")
            
            # Test metadata if playing
            if player_status and player_status.get('status') == 'play':
                metadata = await client.get_track_metadata()
                if metadata:
                    print("   Currently Playing:")
                    print(f"     Title: {metadata.get('title', 'Unknown')}")
                    print(f"     Artist: {metadata.get('artist', 'Unknown')}")
                    print(f"     Album: {metadata.get('album', 'Unknown')}")
            
            print("\n🎉 WiiM device is ready for integration!")
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify the IP address is correct")
        print("   2. Ensure WiiM device is powered on")
        print("   3. Check both devices are on same network")
        print(f"   4. Test web interface: http://{host}/httpapi.asp?command=getStatusEx")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python test_connection.py <WIIM_IP_ADDRESS>")
        print("Example: python test_connection.py 192.168.1.100")
        sys.exit(1)
    
    host = sys.argv[1]
    
    # Validate IP format (basic check)
    parts = host.split('.')
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        print(f"❌ Invalid IP address format: {host}")
        sys.exit(1)
    
    try:
        success = asyncio.run(test_wiim_device(host))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()