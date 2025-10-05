# WiiM Integration for Unfolded Circle Remote Two/3

Control your WiiM audio streaming devices (Mini, Pro, Pro Plus, Ultra, Amp) directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive media player and remote control functionality.

![WiiM](https://img.shields.io/badge/WiiM-Audio%20Streaming-blue)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-wiim)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-wiim/total)
![License](https://img.shields.io/badge/license-MIT-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)

## Features

This integration provides comprehensive control of WiiM audio streaming devices with intelligent capability detection and automatic preset discovery.

### Media Player Functionality

- **Playback Controls**: Play, Pause, Stop, Next, Previous
- **Volume Management**: Volume up/down, mute/unmute with real-time feedback
- **Advanced Controls**: Repeat modes (off/one/all), Shuffle (on/off)
- **Now Playing**: Track title, artist, album information
- **Artwork Display**: Album art and station logos
- **Progress Tracking**: Real-time position and duration (for non-streaming content)
- **Source Selection**: WiFi, Bluetooth, Line-in, Optical, HDMI, Phono, USB inputs
- **Music Services**: Spotify Connect, TIDAL Connect, Pandora, SoundCloud, and all configured services
- **Auto-Play**: Intelligent automatic playback from music services via presets
- **Device Functions**: Display control, device reboot

### Remote Control

- **Physical Button Mapping**: Automatic mapping to Remote Two/3 buttons
  - **Transport**: PLAY, PAUSE, NEXT, PREV buttons
  - **Volume**: VOL+, VOL-, MUTE buttons
  - **D-Pad**: Volume and track navigation
  - **Color Buttons**: Quick access to top 4 music services
  - **Power**: Stop playback (long press for device reboot)
- **Dynamic UI Pages**: 
  - **Main Controls**: Transport and volume controls
  - **Music Services**: Quick access to discovered services
  - **Presets**: One-touch access to all 12 configured presets
  - **Audio Output**: Switch between SPDIF, AUX/Line Out, COAX outputs
  - **Equalizer**: 22+ EQ presets with on/off control
  - **Device Control**: Display settings and system functions
- **Service Commands**: Dedicated commands for each music service
- **Preset Access**: Direct preset activation (1-12)
- **Audio Output Control**: Dynamic output switching based on device capabilities

## Device Compatibility

### Supported WiiM Products
- **WiiM Ultra**: Fully tested and verified
- **WiiM Pro Plus**: Supported
- **WiiM Pro**: Supported
- **WiiM Mini**: Supported
- **WiiM Amp**: Supported

### Network Requirements
- **Local Network**: WiiM device on same network as Remote
- **Static IP**: Recommended for reliability
- **HTTPS API**: Port 443 (automatically configured)
- **No Authentication**: Direct local control via WiiM HTTP API

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-wiim/releases) page
2. Download the latest `uc-intg-wiim-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-wiim:latest`

**Docker Compose:**
```yaml
version: '3.8'
services:
  wiim-integration:
    image: ghcr.io/mase1981/uc-intg-wiim:latest
    container_name: uc-intg-wiim
    restart: unless-stopped
    ports:
      - "9090:9090"
    environment:
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - UC_CONFIG_HOME=/config
      - UC_DISABLE_MDNS_PUBLISH=false
    volumes:
      - ./config:/config
      - /etc/localtime:/etc/localtime:ro
    networks:
      - wiim-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9090/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  wiim-network:
    driver: bridge
```

**Docker Run:**
```bash
docker run -d --name=uc-intg-wiim --network host -v </local/path>:/config --restart unless-stopped ghcr.io/mase1981/uc-intg-wiim:latest
```

## Configuration

### Step 1: Prepare Your WiiM Device

1. **WiiM App Setup:**
   - Ensure WiiM device is fully configured in WiiM Home app
   - Connect device to your network
   - **Important**: Configure presets for music services you want to use
   - Note the device IP address (Settings → Device Info)

2. **Configure Music Service Presets:**
   - Open WiiM Home app
   - Navigate to your favorite music service (Spotify, Pandora, etc.)
   - Find a playlist, station, or album you like
   - **Long-press** one of the 12 preset buttons to save it
   - Repeat for each music service you want to access
   - At least one preset per service is required for service to appear in integration

3. **Find Device IP:**
   - WiiM Home app → Settings → Device → Network Info
   - Note the IP address (e.g., `192.168.1.100`)
   - **Recommended**: Set static IP in your router for reliability

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The WiiM integration should appear in **Available Integrations**
3. Click **"Configure"** and enter:
   - **WiiM Device IP**: IP address of your WiiM device (e.g., `192.168.1.100`)
4. Click **"Complete Setup"** - the integration will:
   - Connect to the WiiM device
   - Discover device capabilities
   - Detect configured presets and music services
   - Create media player and remote entities automatically

### Step 3: Add to Activities

1. Go to **Activities** → **Create New** or edit existing activity
2. Add discovered WiiM entities:
   - **Media Player**: For playback control and source selection
   - **Remote**: For button mapping and UI pages
3. Configure button mappings (auto-populated for physical buttons)
4. Customize UI pages as needed

## Music Services Setup

### Important: Preset Requirement

The WiiM HTTP API **requires presets** to access music services programmatically. Without presets, music services cannot be controlled via the integration.

**Why Presets Are Required:**
- WiiM API does not expose "list of configured services"
- No direct "play Spotify" or "start Pandora" command exists
- Presets are the only API-exposed method to trigger service playback
- This is a WiiM API limitation, not an integration limitation

### How to Configure Service Presets:

1. **Open WiiM Home App**
2. **For Each Service** (Spotify, Pandora, TIDAL, etc.):
   - Navigate to the service
   - Find any playlist, station, or album
   - **Long-press** a preset button (1-12)
   - Save the content as a preset
3. **Restart Integration**
4. **Verify**: Service now appears in source dropdown

### What You Get:

**After configuring presets:**
- Music services appear in Media Player source dropdown
- Selecting "Spotify" plays your first Spotify preset
- Color buttons on Remote mapped to top 4 services
- Service commands available for custom button mapping

**Example Configuration:**
- Preset 1: Spotify playlist → Service "Spotify" appears
- Preset 2: Pandora station → Service "Pandora" appears  
- Preset 3: Another Spotify playlist → Uses same "Spotify" service
- Preset 4: TIDAL album → Service "TIDAL Connect" appears

## Troubleshooting

### Common Issues

**Connection Failed:**
- Verify WiiM device IP is correct and accessible
- Check device is on same network as Remote
- Ensure WiiM device is powered on
- Test device web interface: `https://WIIM_IP/httpapi.asp?command=getStatusEx`
- Check firewall settings between Remote and WiiM

**No Music Services Appearing:**
- **Solution**: Configure presets in WiiM Home app (see Music Services Setup above)
- Verify presets are saved correctly in app
- Restart integration after configuring presets
- Check integration logs for discovered services

**Metadata Not Updating:**
- WiiM devices sometimes return placeholder values ("unknow", "un_known")
- Integration automatically filters these placeholders
- Radio streams may have limited metadata
- Some services provide better metadata than others

**Physical Buttons Not Auto-Mapping:**
- Remove and re-add remote entity to activity
- Ensure remote entity initialization completed
- Check integration status is "Connected"
- Verify button mappings in integration logs

**Audio Output Switching Not Working:**
- Feature availability depends on WiiM device model
- Check device capabilities in WiiM Home app
- Some models support SPDIF, AUX/Line Out, COAX
- Integration automatically detects available outputs

### Debug Information

Enable detailed logging for troubleshooting:

**Docker Environment:**
```bash
# Add to docker-compose.yml environment section
- LOG_LEVEL=DEBUG

# View logs
docker logs uc-intg-wiim
```

**Integration Logs:**
- **Remote Interface**: Settings → Integrations → WiiM → View Logs
- **Common Errors**: Connection, discovery, preset issues

**Network Verification:**
```bash
# Test WiiM device connectivity
ping <device-ip>

# Test WiiM API
curl -k "https://<device-ip>/httpapi.asp?command=getStatusEx"

# Test specific commands
curl -k "https://<device-ip>/httpapi.asp?command=getPlayerStatus"
curl -k "https://<device-ip>/httpapi.asp?command=getPresetInfo"
```

**WiiM App Verification:**
- Verify device accessible in WiiM Home app
- Check presets configured correctly
- Test playback directly in app
- Verify services are linked to your account

## For Developers

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-wiim.git
   cd uc-intg-wiim
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   ```bash
   # Run integration
   python -m uc_intg_wiim.driver
   
   # Integration runs on localhost:9090
   # Configure via Remote interface or curl
   ```

3. **VS Code debugging:**
   - Open project in VS Code
   - Use F5 to start debugging session
   - Configure integration with your WiiM device IP

### Project Structure

```
uc-intg-wiim/
├── uc_intg_wiim/              # Main package
│   ├── __init__.py            # Package info with auto-version
│   ├── client.py              # WiiM HTTP API client
│   ├── config.py              # Configuration management
│   ├── driver.py              # Main integration driver
│   ├── media_player.py        # Media player entity
│   ├── remote.py              # Remote control entity
│   └── setup.py               # Setup flow handler (optional)
├── .github/workflows/         # GitHub Actions CI/CD
│   └── build.yml              # Automated build pipeline
├── docker-compose.yml         # Docker deployment
├── Dockerfile                 # Container build (if applicable)
├── driver.json                # Integration metadata (version source)
├── requirements.txt           # Dependencies
├── pyproject.toml             # Python project config (auto-version)
└── README.md                  # This file
```

### Development Features

#### WiiM HTTP API Implementation
Complete WiiM HTTP API integration:
- **HTTPS Protocol**: SSL-based communication with certificate bypass
- **Capability Detection**: Automatic discovery of device features
- **Preset Discovery**: Dynamic preset and service detection
- **Real-time Updates**: 5-second polling with efficient state management
- **Error Recovery**: Robust connection handling and reconnection

#### Entity Architecture
Production-ready intelligent entities:
- **Dynamic Creation**: Entities created based on device capabilities
- **Button Mapping**: Automatic physical button to command mapping
- **UI Pages**: Dynamic page generation based on discovered features
- **Metadata Handling**: Smart filtering of WiiM placeholder values
- **State Management**: Proper state transitions and clearing

#### Audio Output Control
Dynamic audio output management:
- **Auto-Detection**: Discovers available output modes
- **Fallback Support**: Standard outputs when detection fails
- **Combo Commands**: Input + output switching for activities

### Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test connection to WiiM device
python test_connection.py <WIIM_IP>

# Test API endpoints
python test_wiim_api.py

# Discover services
python wiim_service_discovery.py <WIIM_IP>

# Run integration
python -m uc_intg_wiim.driver
```

### Testing Scripts

**test_connection.py**: Verifies device connectivity and capabilities  
**test_wiim_api.py**: Tests all API endpoints and media information  
**wiim_service_discovery.py**: Comprehensive service and preset discovery

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test with WiiM device
4. Verify all entity types (media player, remote)
5. Test preset discovery and music services
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Credits

- **Developer**: Meir Miyara
- **WiiM Protocol**: Built using WiiM HTTP API
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Community**: Testing and feedback from UC community
- **Testing**: Integration built and tested on WiiM Ultra

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-wiim/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

## Known Limitations

- **Music Services**: Require presets configured in WiiM Home app (WiiM API limitation)
- **Playlists**: UCAPI does not support playlist browsing (auto-plays first song from service)
- **Service Discovery**: Only services with configured presets are detected
- **Metadata**: Some sources provide limited or placeholder metadata
- **Network**: Device must be on same network as Remote
- **Static IP**: Highly recommended for reliable connection

## API Reference

### WiiM HTTP API Endpoints Used

- `getStatusEx` - Device information and status
- `getPlayerStatus` - Current playback state
- `getMetaInfo` - Track metadata
- `getPresetInfo` - User preset configuration
- `EQGetList` - Available equalizer presets
- `getNewAudioOutputHardwareMode` - Audio output capabilities
- `setPlayerCmd:*` - Playback control commands
- `MCUKeyShortClick:{n}` - Preset activation
- `setAudioOutputHardwareMode:{n}` - Output switching

---

**Made with ❤️ for the Unfolded Circle Community**

**Thank You**: Meir Miyara