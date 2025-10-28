# YoLink Multi-Home Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A custom Home Assistant integration that enables **multiple YoLink homes** using User Access Credentials (UAC) authentication.

## Why This Integration?

The official [YoLink integration](https://www.home-assistant.io/integrations/yolink/) only supports a single home per Home Assistant instance. If you have multiple YoLink homes (e.g., primary residence and vacation home), you cannot access devices from both homes simultaneously.

**This custom integration solves that limitation** by using YoLink's UAC (User Access Credentials) authentication instead of OAuth2, where each UAC is tied to a specific home.

## Features

✅ **Multiple YoLink Homes** - Configure as many YoLink homes as you need
✅ **UAC Authentication** - Simple credential-based setup (no OAuth2 flow)
✅ **Full Device Support** - All device types supported by the official integration
✅ **Coexists with Official Integration** - Can run alongside the official YoLink integration
✅ **Auto-Discovery** - Devices automatically discovered and organized by home
✅ **MQTT Push Updates** - Real-time device state updates

## Supported Devices

This integration supports the same devices as the [official YoLink integration](https://www.home-assistant.io/integrations/yolink/):

- Door/Contact Sensors
- Motion Sensors
- Temperature & Humidity Sensors
- Water Leak Sensors
- Smart Locks
- Smart Switches & Outlets
- Garage Door Controllers
- Sirens & Alarms
- Thermostats
- And more...

## Installation

### Via HACS (Recommended)

1. **Install HACS** if you haven't already: https://hacs.xyz/docs/setup/download
2. **Add this repository as a custom repository**:
   - Open HACS
   - Click on "Integrations"
   - Click the three dots in the top right
   - Select "Custom repositories"
   - Enter the URL: `https://github.com/cd1zz/homeassistant-yolink-multi`
   - Category: "Integration"
   - Click "Add"
3. **Install the integration**:
   - Find "YoLink Multi-Home" in HACS
   - Click "Download"
   - Restart Home Assistant

### Manual Installation

1. Download this repository
2. Copy the `custom_components/yolink_multi` directory to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

### Step 1: Create YoLink UAC Credentials

You need to create User Access Credentials (UAC) for each home you want to add:

1. Go to https://www.yosmart.com/user/uac
2. Log in with your YoLink account
3. **Select the home** you want to create credentials for
4. Click "Generate" to create new credentials
5. Copy the **UAID** (User Access ID) and **Secret Key**
6. Repeat for each additional home

**Important:** Each UAC is tied to ONE home. If you have 2 homes, you need 2 sets of credentials.

### Step 2: Add Integration in Home Assistant

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"YoLink Multi-Home"**
4. Enter your UAID and Secret Key from Step 1
5. Click **Submit**
6. Your devices will be automatically discovered

### Step 3: Add Additional Homes (Optional)

To add another YoLink home:

1. Repeat Step 1 to get UAC credentials for your second home
2. In Home Assistant, go to **Settings** → **Devices & Services**
3. Click **"+ Add Integration"** again
4. Search for **"YoLink Multi-Home"**
5. Enter the credentials for your second home
6. Both homes will now be available in Home Assistant!

## How It Works

### Multi-Home Support

Each config entry represents one YoLink home. Devices are uniquely identified using:
```
{home_id}_{device_id}
```

This prevents device ID conflicts when you have the same device types in multiple homes.

### Suggested Areas

Devices are automatically suggested to be placed in an area matching your home name (e.g., "Vacation Home", "Main House"), making it easy to organize your devices.

### Coexistence with Official Integration

This integration uses the domain `yolink_multi`, which is different from the official integration's `yolink` domain. This means:

- ✅ You can run both integrations simultaneously
- ✅ No conflicts with existing YoLink setup
- ✅ You could use OAuth2 for one home and UAC for another

## Differences from Official Integration

| Feature | Official YoLink | YoLink Multi-Home |
|---------|----------------|-------------------|
| Authentication | OAuth2 | UAC (User Access Credentials) |
| Multiple Homes | ❌ Single home only | ✅ Unlimited homes |
| Setup Complexity | Medium (OAuth redirect) | Simple (copy/paste credentials) |
| Device Support | Full | Full (same codebase) |
| Domain | `yolink` | `yolink_multi` |

## Troubleshooting

### "Cannot connect" error during setup

- Verify your UAID and Secret Key are correct
- Ensure your YoLink account has access to the home
- Check your internet connection
- Try regenerating your UAC credentials

### Devices not showing up

- Wait a few minutes for device discovery
- Check that the devices are assigned to the correct home in the YoLink app
- Try reloading the integration

### "Already configured" error

You're trying to add the same home twice. Each home can only be added once.

### Credential expiration

If your credentials expire, Home Assistant will prompt you to reauthenticate:

1. Go to **Settings** → **Devices & Services**
2. Find the YoLink Multi-Home entry showing an error
3. Click **"Reauthenticate"**
4. Enter new UAC credentials for the same home

## FAQ

**Q: Can I use this with the official YoLink integration?**
A: Yes! They use different domains and won't conflict.

**Q: Do I need separate YoLink accounts?**
A: No! You use the same YoLink account. You just create different UAC credentials for each home.

**Q: Will this work with YoLink hubs?**
A: Yes, it works with all YoLink hubs and devices.

**Q: What happens if I delete a device from YoLink app?**
A: The device will be automatically removed from Home Assistant on the next refresh.

**Q: Can I rename devices?**
A: Yes, you can rename devices in Home Assistant just like any other entity.

## Support

- **Issues**: https://github.com/cd1zz/homeassistant-yolink-multi/issues
- **Home Assistant Community**: https://community.home-assistant.io/
- **YoLink Support**: https://support.yosmart.com/

## Credits

This integration is based on the official [Home Assistant YoLink integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/yolink) by [@matrixd2](https://github.com/matrixd2).

**Modifications:**
- Added UAC authentication support
- Implemented multi-home functionality
- Updated device identifiers to support multiple homes
- Simplified configuration flow

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

This is a derivative work of the Home Assistant YoLink integration, licensed under Apache 2.0.
