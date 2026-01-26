# WiiM Integration for Unfolded Circle Remote 2/3

Control your WiiM audio streaming devices (Mini, Pro, Pro Plus, Ultra, Amp) directly from your Unfolded Circle Remote 2 or Remote 3 with **comprehensive media player control**, **automatic service discovery**, and **intelligent preset management**.

![WiiM](https://img.shields.io/badge/WiiM-Audio%20Streaming-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-wiim?style=flat-square)](https://github.com/mase1981/uc-intg-wiim/releases)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-wiim?style=flat-square)](https://github.com/mase1981/uc-intg-wiim/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-wiim/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive control of WiiM audio streaming devices through the WiiM HTTP API, delivering seamless integration with your Unfolded Circle Remote for complete music control with intelligent capability detection and automatic preset discovery.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 🎵 **Media Player Functionality**

#### **Playback Controls**
- **Play/Pause/Stop** - Full playback control
- **Next/Previous** - Track navigation
- **Repeat Modes** - Off/One/All
- **Shuffle** - On/Off control
- **Real-time Updates** - 5-second polling

#### **Volume Management**
- **Volume Up/Down** - Precise volume control
- **Set Volume** - Direct volume control (0-100)
- **Volume Slider** - Visual volume control
- **Mute/Unmute** - Quick mute toggle
- **Real-time Feedback** - Instant volume updates

#### **Media Information**
- **Now Playing** - Track title, artist, album
- **Artwork Display** - Album art and station logos
- **Progress Tracking** - Real-time position and duration
- **Source Display** - Current input/service

#### **Source Selection**
- **Physical Inputs** - WiFi, Bluetooth, Line-in, Optical, HDMI, Phono, USB
- **Music Services** - Spotify Connect, TIDAL Connect, Pandora, SoundCloud
- **Auto-Play** - Intelligent automatic playback via presets
- **Service Discovery** - Automatic detection from configured presets

### 🎮 **Remote Control Features**

#### **Physical Button Mapping**
Automatic mapping to Remote 2/3 buttons:
- **Transport**: PLAY, PAUSE, NEXT, PREV
- **Volume**: VOL+, VOL-, MUTE
- **D-Pad**: Volume and track navigation
- **Color Buttons**: Quick access to top 4 music services
- **Power**: Stop playback (long press for reboot)

#### **Dynamic UI Pages**
- **Main Controls**: Transport and volume
- **Music Services**: Quick access to discovered services
- **Presets**: One-touch access to all 12 configured presets
- **Audio Output**: Switch between SPDIF, AUX/Line Out, COAX
- **Equalizer**: 22+ EQ presets with on/off control
- **Device Control**: Display settings and system functions

### **Device Compatibility**

#### **Supported WiiM Products**
- **WiiM Ultra** - Fully tested and verified
- **WiiM Pro Plus** - Supported
- **WiiM Pro** - Supported
- **WiiM Mini** - Supported
- **WiiM Amp** - Supported

### **Protocol Requirements**

- **Protocol**: WiiM HTTP API
- **HTTPS Port**: 443 (automatically configured)
- **Authentication**: None (direct local control)
- **Network Access**: Device must be on same local network
- **Capability Detection**: Automatic discovery

### **Network Requirements**

- **Local Network Access** - Integration requires same network as WiiM device
- **HTTPS Protocol** - WiiM HTTP API (port 443)
- **Static IP Recommended** - Device should have static IP or DHCP reservation
- **Firewall** - Must allow HTTPS traffic
- **No Authentication** - Direct local control

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
services:
  uc-intg-wiim:
    image: ghcr.io/mase1981/uc-intg-wiim:latest
    container_name: uc-intg-wiim
    network_mode: host
    volumes:
      - </local/path>:/config
    environment:
      - UC_CONFIG_HOME=/config
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-intg-wiim --restart unless-stopped --network host -v wiim-config:/config -e UC_CONFIG_HOME=/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-wiim:latest
```

## Configuration

### Step 1: Prepare Your WiiM Device

**IMPORTANT**: WiiM device must be powered on and connected to your network before adding the integration.

#### WiiM App Setup:
1. Ensure WiiM device is fully configured in WiiM Home app
2. Connect device to your network
3. **Important**: Configure presets for music services you want to use
4. Note the device IP address (Settings → Device Info)

#### Configure Music Service Presets:
1. Open WiiM Home app
2. Navigate to your favorite music service (Spotify, Pandora, etc.)
3. Find a playlist, station, or album you like
4. **Long-press** one of the 12 preset buttons to save it
5. Repeat for each music service you want to access
6. At least one preset per service is required for service to appear in integration

#### Find Device IP:
- WiiM Home app → Settings → Device → Network Info
- Note the IP address (e.g., `192.168.1.100`)
- **Recommended**: Set static IP in your router for reliability

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The WiiM integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Configuration:**
- **WiiM Device IP**: IP address of your WiiM device (e.g., `192.168.1.100`)
- Click **Complete Setup**

#### **Connection Test:**
- Integration will connect to the WiiM device
- Discover device capabilities
- Detect configured presets and music services
- Setup fails if device unreachable

4. Integration will create entities:
   - **Media Player**: Playback control and source selection
   - **Remote**: Button mapping and UI pages

## Using the Integration

### Music Services Setup

**Important: Preset Requirement**

The WiiM HTTP API **requires presets** to access music services programmatically. Without presets, music services cannot be controlled via the integration.

**Why Presets Are Required:**
- WiiM API does not expose "list of configured services"
- No direct "play Spotify" or "start Pandora" command exists
- Presets are the only API-exposed method to trigger service playback
- This is a WiiM API limitation, not an integration limitation

**How to Configure Service Presets:**
1. Open WiiM Home App
2. For Each Service (Spotify, Pandora, TIDAL, etc.):
   - Navigate to the service
   - Find any playlist, station, or album
   - **Long-press** a preset button (1-12)
   - Save the content as a preset
3. Restart Integration
4. Verify: Service now appears in source dropdown

**What You Get:**
- Music services appear in Media Player source dropdown
- Selecting "Spotify" plays your first Spotify preset
- Color buttons on Remote mapped to top 4 services
- Service commands available for custom button mapping

**Example Configuration:**
- Preset 1: Spotify playlist → Service "Spotify" appears
- Preset 2: Pandora station → Service "Pandora" appears
- Preset 3: Another Spotify playlist → Uses same "Spotify" service
- Preset 4: TIDAL album → Service "TIDAL Connect" appears

### Media Player Entity

The media player entity provides comprehensive control:

- **Playback Control**: Play, Pause, Stop, Next, Previous
- **Volume Control**: Volume slider, Up/Down, Mute toggle
- **Source Selection**: Physical inputs and music services
- **Media Information**: Title, Artist, Album, Artwork
- **Advanced Features**: Repeat, Shuffle, Seek

### Remote Entity

The remote entity provides UI pages and button mapping:

- **Main Controls**: Transport and volume controls
- **Music Services**: Quick access to discovered services
- **Presets**: One-touch access to all 12 presets
- **Audio Output**: Dynamic output switching
- **Equalizer**: EQ presets with on/off control
- **Device Control**: Display and system functions

## Credits

- **Developer**: Meir Miyara
- **WiiM Protocol**: Built using WiiM HTTP API
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Protocol**: WiiM HTTP API
- **Community**: Testing and feedback from UC community
- **Testing**: Integration built and tested on WiiM Ultra

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-wiim/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **WiiM Support**: [Official WiiM Support](https://www.wiimhome.com/support)

---

**Made with ❤️ for the Unfolded Circle and WiiM Communities**

**Thank You**: Meir Miyara
