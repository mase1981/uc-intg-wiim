# WiiM Integration for Unfolded Circle Remote Two

[![GitHub Release](https://img.shields.io/github/release/mase1981/uc-intg-wiim.svg)](https://github.com/mase1981/uc-intg-wiim/releases)
[![GitHub License](https://img.shields.io/github/license/mase1981/uc-intg-wiim.svg)](https://github.com/mase1981/uc-intg-wiim/blob/main/LICENSE)

Custom integration for controlling WiiM audio streaming devices (Mini, Pro, Pro Plus, Ultra, Amp) with your Unfolded Circle Remote Two/3.
<p>

**NOTE:**  This integration was built and tested on WiiM Ultra, but should work for all the rest is it was build to detect and build during configuration.

## 🎵 Features

### Media Player Control
- **Full Playback Control**: Play, pause, stop, next, previous, seek
- **Volume Management**: Volume up/down, mute/unmute with real-time feedback
- **Advanced Controls**: Repeat modes, shuffle, source switching
- **Live Metadata**: Track title, artist, album, artwork display
- **Progress Tracking**: Real-time position and duration updates

### Source Management
- **Multi-Input Support**: WiFi, Bluetooth, Line-in, Optical, HDMI, Phono, USB
- **Service Integration**: Spotify Connect, TIDAL Connect, AirPlay, DLNA
- **Smart Discovery**: Automatic detection of available sources per device

### Remote Control Interface
- **4-Page Layout**: Organized transport, sources, presets, and EQ controls
- **Dynamic UI**: Pages adapt based on device capabilities
- **Preset Support**: Up to 12 user-configured presets with service detection
- **EQ Management**: Full equalizer control with 22+ preset options

### Awesome Features
- **Auto-Discovery**: Automatic capability detection during setup
- **Real-time Updates**: 5-second polling with efficient state management
- **Error Recovery**: Robust connection handling and automatic reconnection
- **Zero Configuration**: Single IP input setup process
<p>

**NOTE:** For best results use a static IP

## 📋 Prerequisites

### Hardware Requirements
- **WiiM Device**: Mini, Pro, Pro Plus, Ultra, or Amp (Integration was tested and built using Ultra)
- **Remote Two/3**: Unfolded Circle Remote Two/3
- **Network**: Both devices on same local network (Must)
- **Firewall**: Ensure no WiiM specific ports blocked between Remote and WiiM products

### Software Requirements (Development)
- **Python**: 3.11 or higher
- **Development Environment**: Visual Studio Code (recommended)
- **Operating System**: Windows 10/11, macOS, or Linux

### WiiM Device Setup
1. Configure WiiM device using official WiiM Home app
2. Ensure device is connected to your local network
3. Note the device's IP address from your router or app
4. Test device accessibility: `http://YOUR_WIIM_IP/httpapi.asp?command=getStatusEx`

## 🚀 Quick Start

### Installation via Remote Two/3 Web Interface

1. **Access Web Configurator**
   ```
   http://YOUR_REMOTE_IP/configurator
   ```

2. **Install Integration**
   - Navigate to: **Integrations** → **Available** / **Add New** → **Custom**
   - Find: **WiiM Integration**
   - Click: **Install**

3. **Configure Device**
   - Enter your WiiM device IP address
   - Click: **Continue**
   - Wait for automatic device discovery
   - Complete setup
   - Add the entities (Media Player / Remote)
<p>

**NOTE**: you might need to wait a few seconds for the integration to switch to "Connected"

4. **Add to Activities**
   - Go to: **Activities** → **Create New**
   - Add discovered WiiM entities
   - Configure remote layouts as needed

## 🛠️ Development Setup

### Local Development Environment

```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-wiim.git
cd uc-intg-wiim

# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Testing Connection

```bash
# Test WiiM device connectivity
python -c "
import asyncio
from uc_intg_wiim.client import WiiMClient

async def test():
    async with WiiMClient('YOUR_WIIM_IP') as client:
        info = await client.get_device_info()
        print(f'Connected to: {info.get(\"DeviceName\", \"Unknown\")}')

asyncio.run(test())
"
```

### Debug with Visual Studio Code

1. **Open Project**: `code .`
2. **Configure Launch**: Use provided `.vscode/launch.json`
3. **Start Debugging**: Press `F5`
4. **Monitor Logs**: Check Debug Console for detailed output

### Manual Execution

```bash
# Run integration directly
python -m uc_intg_wiim.driver

# With debug logging
UC_INTEGRATION_HTTP_PORT=9090 python -m uc_intg_wiim.driver
```

## 📁 Project Structure

```
uc-intg-wiim/
├── .github/workflows/
│   └── build.yml              # GitHub Actions build configuration
├── .vscode/
│   └── launch.json            # VS Code debug configuration
├── uc_intg_wiim/
│   ├── __init__.py            # Package initialization
│   ├── client.py              # WiiM HTTP API client
│   ├── config.py              # Configuration management
│   ├── driver.py              # Main integration driver
│   ├── media_player.py        # Media player entity implementation
│   ├── remote.py              # Remote control entity implementation
│   └── setup.py               # Setup handler (optional)
├── driver.json                # Integration metadata
├── pyproject.toml             # Python project configuration
├── requirements.txt           # Python dependencies
├── README.md                  # This documentation
└── LICENSE                    # MIT license
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UC_INTEGRATION_HTTP_PORT` | Integration HTTP port | `9090` |
| `UC_INTEGRATION_INTERFACE` | Bind interface | `0.0.0.0` |
| `UC_CONFIG_HOME` | Configuration directory | `./config` |
| `UC_DISABLE_MDNS_PUBLISH` | Disable mDNS publishing | `false` |

### Configuration File

Located at: `config/config.json`

```json
{
  "host": "192.168.1.100"
}
```

## 🐛 Troubleshooting

### Setup Issues

**Problem**: Integration setup fails with connection error

**Solution**:
1. Verify WiiM device IP address
2. Test device web interface: `http://WIIM_IP/httpapi.asp?command=getStatusEx`
3. Ensure both devices on same network
4. Check firewall settings
5. Restart WiiM device if necessary

**Problem**: Entities not appearing in Remote Two

**Solution**:
1. Complete setup process fully
2. Restart integration via web configurator
3. Check integration logs for errors
4. Verify device discovery completed successfully

### Runtime Issues

**Problem**: Media player shows "Unavailable"

**Solution**:
1. Check network connectivity between devices
2. Verify WiiM device is powered on
3. Test API accessibility manually
4. Check for IP address changes

**Problem**: Remote commands not working

**Solution**:
1. Ensure WiiM device supports the specific command
2. Check device capability discovery in logs
3. Verify command syntax in remote UI
4. Test commands via WiiM Home app

**Problem**: Missing metadata or artwork

**Solution**:
1. Verify content source provides metadata
2. Check WiiM Home app for same information
3. Ensure stable internet connection
4. Some sources may have limited metadata

### Debug Information

**Enable detailed logging**:
```bash
# Set logging level in driver.py
logging.basicConfig(level=logging.DEBUG)
```

**Check integration status**:
```bash
# Via web configurator
http://YOUR_REMOTE_IP/configurator → Integrations → WiiM → Status
```

**API Testing**:
```bash
# Test device responses
curl "http://WIIM_IP/httpapi.asp?command=getStatusEx"
curl "http://WIIM_IP/httpapi.asp?command=getPlayerStatus"
curl "http://WIIM_IP/httpapi.asp?command=getMetaInfo"
```

## 🔄 Building and Deployment

### GitHub Actions Build

The integration includes automated building via GitHub Actions:

```yaml
# Triggered on:
- Push to main branch
- Pull requests
- Manual workflow dispatch
- Release creation
```

**Build artifacts**:
- `uc-intg-wiim.tar.gz` - Installation package
- `uc-intg-wiim-docker.tar.gz` - Docker image

### Manual Build

```bash
# Install build dependencies
pip install build twine

# Build distribution
python -m build

# Create installation package
tar -czf uc-intg-wiim.tar.gz \
  driver.json \
  uc_intg_wiim/ \
  requirements.txt
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  wiim-integration:
    image: ghcr.io/mase1981/uc-intg-wiim:latest
    ports:
      - "9090:9090"
    environment:
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_CONFIG_HOME=/config
    volumes:
      - ./config:/config
    restart: unless-stopped
```

```bash
# Deploy with Docker Compose
docker-compose up -d
```

## 📚 API Reference

### WiiM HTTP API Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `getStatusEx` | Device information | JSON device status |
| `getPlayerStatus` | Playback status | JSON player state |
| `getMetaInfo` | Track metadata | JSON metadata |
| `getPresetInfo` | User presets | JSON preset list |
| `EQGetList` | EQ presets | JSON equalizer options |
| `setPlayerCmd:*` | Control commands | Status confirmation |

### Integration API Events

- **Entity Updates**: Real-time state synchronization
- **Command Responses**: Immediate feedback
- **Error Handling**: Graceful degradation
- **Discovery Events**: Dynamic capability detection

## 🤝 Contributing

### Development Workflow

1. **Fork Repository**
   ```bash
   gh repo fork mase1981/uc-intg-wiim
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-enhancement
   ```

3. **Make Changes**
   - Follow existing code patterns
   - Add appropriate logging
   - Update documentation

4. **Test Thoroughly**
   ```bash
   # Run integration locally
   python -m uc_intg_wiim.driver
   
   # Test with actual WiiM device
   # Verify all entity types
   # Check error scenarios
   ```

5. **Submit Pull Request**
   - Include detailed description
   - Reference related issues
   - Ensure CI passes

### Code Standards

- **Python Style**: Follow PEP 8
- **Type Hints**: Use throughout codebase
- **Error Handling**: Comprehensive exception management
- **Logging**: Appropriate levels and messages
- **Documentation**: Clear docstrings and comments

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Community Resources

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-wiim/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **WiiM Support**: [Official device support](https://support.wiim.com/)

### Professional Support

For enterprise deployments or professional integration services, contact the development team through GitHub.

---

**Made with ❤️ for the Unfolded Circle Community**

*Enjoy seamless WiiM control with your Remote Two/3!*
<p>

**Thank You**: Meir Miyara