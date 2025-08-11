#!/usr/bin/env python3
"""
WiiM API Test Script - Check what media information is available.

Run this script to see what your WiiM device actually returns.
"""

import asyncio
import json
import ssl
import aiohttp

# Your WiiM device IP
WIIM_HOST = "10.2.9.193"

async def test_wiim_api():
    """Test WiiM API endpoints to see what media info is available."""
    
    # Create SSL context that ignores certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        
        print(f"Testing WiiM device at: {WIIM_HOST}")
        print("=" * 50)
        
        # Test endpoints
        endpoints = [
            ("Device Status", "getStatusEx"),
            ("Player Status", "getPlayerStatus"), 
            ("Current Track Metadata", "getMetaInfo"),
            ("Preset Info", "getPresetInfo"),
            ("EQ List", "EQGetList")
        ]
        
        for name, command in endpoints:
            print(f"\n🔍 Testing: {name}")
            print(f"Command: {command}")
            print("-" * 30)
            
            try:
                # Try HTTPS first
                https_url = f"https://{WIIM_HOST}/httpapi.asp?command={command}"
                print(f"HTTPS URL: {https_url}")
                
                async with session.get(https_url, ssl=ssl_context) as response:
                    if response.status == 200:
                        text = await response.text()
                        print(f"✅ HTTPS Success (Status: {response.status})")
                        
                        # Try to parse as JSON
                        try:
                            data = json.loads(text)
                            print("📋 JSON Response:")
                            print(json.dumps(data, indent=2, ensure_ascii=False))
                        except json.JSONDecodeError:
                            print("📋 Plain Text Response:")
                            print(f"'{text}'")
                    else:
                        print(f"❌ HTTPS Failed (Status: {response.status})")
                        
                        # Try HTTP fallback
                        http_url = f"http://{WIIM_HOST}/httpapi.asp?command={command}"
                        print(f"Trying HTTP fallback: {http_url}")
                        
                        async with session.get(http_url) as http_response:
                            if http_response.status == 200:
                                text = await http_response.text()
                                print(f"✅ HTTP Success (Status: {http_response.status})")
                                
                                try:
                                    data = json.loads(text)
                                    print("📋 JSON Response:")
                                    print(json.dumps(data, indent=2, ensure_ascii=False))
                                except json.JSONDecodeError:
                                    print("📋 Plain Text Response:")
                                    print(f"'{text}'")
                            else:
                                print(f"❌ HTTP Also Failed (Status: {http_response.status})")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 MEDIA PLAYER ANALYSIS:")
        print("=" * 50)
        
        # Specific analysis for media player viability
        try:
            meta_url = f"https://{WIIM_HOST}/httpapi.asp?command=getMetaInfo"
            async with session.get(meta_url, ssl=ssl_context) as response:
                if response.status == 200:
                    text = await response.text()
                    try:
                        meta_data = json.loads(text)
                        
                        print("🎵 MEDIA INFO AVAILABLE:")
                        if "metaData" in meta_data:
                            metadata = meta_data["metaData"]
                            available_fields = []
                            
                            # Check for useful media fields
                            media_fields = {
                                "title": "Track Title",
                                "artist": "Artist Name", 
                                "album": "Album Name",
                                "albumArtURI": "Album Artwork URL",
                                "genre": "Genre",
                                "duration": "Duration"
                            }
                            
                            for field, description in media_fields.items():
                                if field in metadata and metadata[field]:
                                    available_fields.append(f"  ✅ {description}: {metadata[field]}")
                                else:
                                    available_fields.append(f"  ❌ {description}: Not available")
                            
                            print("\n".join(available_fields))
                            
                            # Decision
                            useful_fields = ["title", "artist", "album"]
                            has_useful_info = any(field in metadata and metadata[field] 
                                                for field in useful_fields)
                            
                            print(f"\n🎯 RECOMMENDATION:")
                            if has_useful_info:
                                print("   ✅ KEEP MEDIA PLAYER - Useful media info available")
                                print("   📱 Media player entity provides value")
                            else:
                                print("   ❌ REMOVE MEDIA PLAYER - No useful media info")
                                print("   📱 Media player entity has no value")
                                print("   🎮 Keep only remote entity for source control")
                        else:
                            print("   ❌ No metaData field found")
                            print("   🎯 RECOMMENDATION: Remove media player entity")
                    except json.JSONDecodeError:
                        print("   ❌ Invalid JSON response")
                        print("   🎯 RECOMMENDATION: Remove media player entity")
                else:
                    print(f"   ❌ Failed to get metadata (Status: {response.status})")
                    print("   🎯 RECOMMENDATION: Remove media player entity")
                    
        except Exception as e:
            print(f"   ❌ Error testing metadata: {e}")
            print("   🎯 RECOMMENDATION: Remove media player entity")

if __name__ == "__main__":
    print("🎵 WiiM Device API Test")
    print("📡 Testing media information capabilities...")
    print()
    
    # Make sure something is playing for best results
    print("💡 TIP: Start playing music on your WiiM device for best test results!")
    print()
    
    try:
        asyncio.run(test_wiim_api())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
    
    print("\n✅ Test complete!")