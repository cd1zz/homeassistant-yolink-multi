# Push to GitHub Instructions

## 1. Create the GitHub Repository

Go to GitHub and create a new repository:
- Name: `homeassistant-yolink-multi`
- Description: "YoLink Multi-Home integration for Home Assistant - supports multiple homes using UAC authentication"
- Public repository
- **Do NOT** initialize with README, .gitignore, or license (we already have those)

## 2. Push the Code

Once the repo is created, run these commands from `/home/user/yolink-multi/`:

```bash
# Add the remote
git remote add origin git@github.com:cd1zz/homeassistant-yolink-multi.git

# Push to main branch
git push -u origin main
```

## 3. Verify on GitHub

Check that all files are visible on GitHub:
- https://github.com/cd1zz/homeassistant-yolink-multi

## 4. Install in Home Assistant

### Option A: Manual Install (for testing)
```bash
# On your HA server
cd /config  # or wherever your HA config is
mkdir -p custom_components
cd custom_components
git clone https://github.com/cd1zz/homeassistant-yolink-multi.git temp
mv temp/custom_components/yolink_multi .
rm -rf temp
```

### Option B: Via HACS (once tested)
1. In Home Assistant, go to HACS → Integrations
2. Click the three dots → Custom repositories
3. Add: `https://github.com/cd1zz/homeassistant-yolink-multi`
4. Category: Integration
5. Search for "YoLink Multi-Home" and install

## 5. Add Integration

1. Settings → Devices & Services
2. Add Integration
3. Search for "YoLink Multi-Home"
4. Enter your UAID: `ua_803F6E8B74DC42E19A9572DB8482991F`
5. Enter your Secret Key: `sec_v1_o5iHUZROc8fvtoIdn1Fz7w==`
6. Submit!

Your devices should appear within 1-2 minutes.
