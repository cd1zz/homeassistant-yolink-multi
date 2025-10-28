# Testing Guide for YoLink Multi-Home

## Prerequisites

1. At least one YoLink home with devices
2. YoLink UAC credentials (UAID + Secret Key)
3. Home Assistant instance for testing

## Initial Setup

### Step 1: Install in Home Assistant

**Option A: Manual Installation (for testing)**
```bash
# From your Home Assistant config directory
mkdir -p custom_components
cp -r /path/to/yolink-multi/custom_components/yolink_multi custom_components/
```

**Option B: Symlink (for development)**
```bash
cd /path/to/homeassistant/config/custom_components
ln -s /path/to/yolink-multi/custom_components/yolink_multi yolink_multi
```

### Step 2: Restart Home Assistant

After copying the files, restart Home Assistant completely.

### Step 3: Check Logs

Watch the logs for any errors:
```bash
tail -f /path/to/homeassistant/home-assistant.log | grep yolink_multi
```

## Testing Checklist

### ✅ Config Flow Testing

- [ ] Integration appears in Settings → Devices & Services
- [ ] Can search for "YoLink Multi-Home"
- [ ] Config form shows UAID and Secret Key fields
- [ ] Invalid credentials show error message
- [ ] Valid credentials create config entry successfully
- [ ] Home name appears as integration title
- [ ] Cannot add same home twice (shows "already configured")

### ✅ Device Discovery

- [ ] All devices from YoLink home appear in HA
- [ ] Device names match YoLink app
- [ ] Devices are organized under correct integration
- [ ] Device identifiers include home_id prefix

### ✅ Entity Creation

For each device type you have, verify:
- [ ] Binary sensors (door/motion/leak sensors)
- [ ] Sensors (temperature/humidity/battery)
- [ ] Switches
- [ ] Locks
- [ ] Climate (thermostats)
- [ ] Covers (garage doors)
- [ ] Other device types

### ✅ State Updates

- [ ] Initial states are correct
- [ ] States update when device changes in YoLink app
- [ ] MQTT messages received and processed
- [ ] Battery levels display correctly
- [ ] Online/offline status tracked

### ✅ Multi-Home Testing

If you have access to multiple homes:
- [ ] Can add second home with different UAC credentials
- [ ] Both homes show as separate integrations
- [ ] Devices from different homes don't conflict
- [ ] Can have same device type in both homes
- [ ] Each home's devices clearly identifiable

### ✅ Reload/Restart Testing

- [ ] Integration survives HA restart
- [ ] Devices remain after restart
- [ ] States restore correctly
- [ ] Can reload integration without errors

### ✅ Removal Testing

- [ ] Can remove integration cleanly
- [ ] All devices/entities removed
- [ ] No errors in logs after removal
- [ ] Can re-add integration after removal

### ✅ Reauthentication

To test credential expiration:
- [ ] Manually trigger reauth (change credentials in YoLink)
- [ ] Reauth notification appears in HA
- [ ] Can update credentials successfully
- [ ] Integration continues working after reauth

### ✅ Error Handling

- [ ] Network timeout handled gracefully
- [ ] Invalid credentials show helpful error
- [ ] Device offline shows unavailable (not error)
- [ ] Integration failure doesn't crash HA

## Common Issues During Testing

### Import Errors

If you see `ModuleNotFoundError: No module named 'yolink'`:
```bash
# Install the yolink-api library
pip install yolink-api==0.5.8
```

### Integration Not Found

- Verify files are in correct location: `config/custom_components/yolink_multi/`
- Check manifest.json is valid JSON
- Restart Home Assistant completely (not just reload)

### No Devices Discovered

- Check UAC credentials are correct
- Verify devices are assigned to the correct home in YoLink app
- Check Home Assistant logs for API errors
- Wait 2-3 minutes for discovery to complete

## Reporting Issues

When reporting issues, include:

1. **Home Assistant Version**: Settings → System → About
2. **Integration Version**: From manifest.json
3. **Error Logs**: Relevant lines from home-assistant.log
4. **Device Type**: Which YoLink devices are involved
5. **Steps to Reproduce**: Clear steps to trigger the issue

## Next Steps

Once basic testing is complete:
1. Test with your second home (if available)
2. Document any device-specific behaviors
3. Create GitHub repository
4. Submit to HACS

