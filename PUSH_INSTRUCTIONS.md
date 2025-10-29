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

## 5. Create UAC Credentials

In the YoLink mobile app:
1. Open YoLink app
2. Go to [Account] → [Advanced Settings] → [Personal Access Credentials]
3. Tap [+] to create new credentials
4. Make sure you're viewing the correct home first
5. Copy the UAID and Secret Key

Docs: http://doc.yosmart.com/docs/overall/qsg_uac/

## 6. Add Integration

1. Settings → Devices & Services
2. Add Integration
3. Search for "YoLink Multi-Home"
4. Enter your UAID and Secret Key
5. Submit!

Your devices should appear within 1-2 minutes.

To add additional homes, repeat steps 5-6 with new credentials for each home.
