# WiiM Integration for Unfolded Circle Remote 2/3

Control your WiiM audio streaming devices (Mini, Pro, Pro Plus, Ultra, Amp) directly from your Unfolded Circle Remote 2 or Remote 3 with **comprehensive media player control**, **media browser**, and **intelligent preset management**.

![WiiM](https://img.shields.io/badge/WiiM-Audio%20Streaming-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-wiim?style=flat-square)](https://github.com/mase1981/uc-intg-wiim/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-wiim?style=flat-square)](https://github.com/mase1981/uc-intg-wiim/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-wiim/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

## Features

### 🎵 Media Player

- **Playback Controls** — Play/Pause, Stop, Next, Previous, Repeat, Shuffle
- **Volume Management** — Volume slider, Up/Down, Mute toggle
- **Media Information** — Now Playing with title, artist, album, artwork, progress tracking
- **Source Selection** — Physical inputs (WiFi, Bluetooth, Line In, Optical, HDMI, Phono, USB) and music services (Spotify Connect, TIDAL Connect, and more)
- **Real-time Updates** — 5-second polling with instant state feedback

### 📂 Media Browser

Browse and play your WiiM content directly from the Remote's media browser interface:

- **Presets** — Browse all configured presets with names, sources, and thumbnails. Tap to play instantly.
- **Sources** — Browse and switch between all available physical inputs and discovered music services.
- **Search** — Search across presets and sources by name.

### 🎮 Remote Control

- **Physical Button Mapping** — Transport (Play, Pause, Next, Prev), Volume (Up, Down, Mute), D-Pad navigation, Power (Stop / long-press Reboot)
- **Dynamic UI Pages** — Main Controls, Sources, Presets, Audio Output, Equalizer, Device Control
- **22+ EQ Presets** — Full equalizer control with on/off toggle

### 📊 Sensors

- **Firmware Version** — Current device firmware
- **Device Model** — Hardware model identification
- **WiFi Network** — Connected SSID
- **IP Address** — Device network address
- **Current Source** — Active input/playback mode

### 🎛️ Select Entities

- **Equalizer** — Browse and select EQ presets
- **Audio Output** — Switch between SPDIF, AUX/Line Out, COAX, BT Source, Audio Cast

### Device Compatibility

| Device | Status |
|---|---|
| WiiM Ultra | Fully tested and verified |
| WiiM Pro Plus | Supported |
| WiiM Pro | Supported |
| WiiM Mini | Supported |
| WiiM Amp | Supported |

### Network Requirements

- Local network access (same network as WiiM device)
- HTTPS protocol (port 443, automatically configured)
- No authentication required (direct local control)
- Static IP or DHCP reservation recommended

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-wiim/releases) page
2. Download the latest `uc-intg-wiim-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

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

## Configuration

### Step 1: Prepare Your WiiM Device

1. Ensure WiiM device is fully configured in WiiM Home app
2. Connect device to your network
3. Configure presets for music services you want to use (required for service discovery)
4. Note the device IP address (Settings → Device Info)

### Step 2: Configure Music Service Presets

The WiiM HTTP API requires presets to access music services programmatically:

1. Open WiiM Home app
2. Navigate to your favorite music service (Spotify, Pandora, etc.)
3. Find a playlist, station, or album
4. **Long-press** one of the 12 preset buttons to save it
5. Repeat for each music service you want to access
6. At least one preset per service is required for the service to appear in the integration

### Step 3: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The WiiM integration should appear in **Available Integrations**
3. Click **Configure** and enter your WiiM device IP address
4. Integration will connect, discover capabilities, detect presets and services

Created entities:
- **Media Player** — Playback control, source selection, media browser
- **Remote** — Button mapping and UI pages
- **Sensors** — Firmware, model, WiFi, IP, current source
- **Selects** — Equalizer and audio output (if device supports them)

## Using the Integration

### Media Browser

Access the media browser from the media player entity on your Remote:

1. Open the WiiM media player entity
2. Tap the **Browse** button
3. Navigate through **Presets** or **Sources**
4. Tap any item to play it instantly
5. Use **Search** to find presets or sources by name

### Music Services

Music services appear in the source dropdown when at least one preset is configured per service. Selecting a service plays its first configured preset.

## Credits

- **Developer**: Meir Miyara
- **Protocol**: WiiM HTTP API
- **Framework**: Unfolded Circle ucapi-framework
- **Community**: Testing and feedback from UC community
- **Testing**: Built and tested on WiiM Ultra

## License

This project is licensed under the MPL-2.0 License - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-wiim/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **WiiM Support**: [Official WiiM Support](https://www.wiimhome.com/support)

---

**Made with ❤️ for the Unfolded Circle and WiiM Communities — Thank You: Meir Miyara**
