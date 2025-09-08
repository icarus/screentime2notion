# iOS Screen Time Data Setup

Your ScreenTime2Notion application now supports iOS device data! Here's how to set it up and what to expect.

## ✅ What's Already Implemented

- **Multi-device support**: Automatically detects iPhone, iPad, Apple Watch, and Apple TV usage
- **Web usage data**: Captures URLs from Safari usage on iOS devices
- **Device identification**: Shows device names with emojis (📱 iPhone 15 Pro, 📱 iPad Pro 12.9", etc.)
- **Combined data processing**: Merges Mac, iPhone, and iPad usage into unified reports

## 🔧 How to Enable iOS Data

### 1. Enable Screen Time on iOS
- Open **Settings** on your iPhone/iPad
- Go to **Screen Time**
- Turn on **Screen Time** if not already enabled

### 2. Enable Cross-Device Sync
- In **Settings → Screen Time**
- Tap **Share Across Devices**
- Turn **ON** the toggle

### 3. Enable on Mac
- Open **System Settings** (or System Preferences on older macOS)
- Go to **Screen Time**
- Click **Options**
- Turn **ON** "Share Across Devices"

### 4. Wait for Sync
- Data synchronization can take **several hours** to complete
- Both devices must be signed into the same Apple ID
- Both devices should be connected to Wi-Fi

## 📊 What Data You'll Get

### App Usage Data
```
📱 iPhone 15 Pro: 8.5h (45 sessions)
📱 iPad Pro: 3.2h (12 sessions) 
💻 Mac: 6.8h (28 sessions)
```

### Web Usage Data (with URLs)
```
🌐 Safari → https://www.github.com (15.2 min)
🌐 Safari → https://www.google.com (8.7 min)
```

### Popular iOS Apps Detected
- Instagram, Twitter, TikTok
- Messages, Mail, Notes
- Spotify, YouTube Music
- Safari (with website URLs)
- And many more...

## 🧪 Testing iOS Functionality

You can test the iOS functionality right now with simulated data:

```bash
# Demo what iOS data looks like
python -m src.main demo-ios --days 3

# Test with simulated multi-device data
python -m src.main test --days 7 --sync
```

## 🔍 Troubleshooting

### No iOS Data Showing Up?
1. **Check if Screen Time is enabled** on your iOS devices
2. **Verify "Share Across Devices" is ON** on both Mac and iOS
3. **Ensure same Apple ID** is signed in on all devices
4. **Wait longer** - sync can take 6-24 hours initially
5. **Check available devices**: `python -m src.main devices`

### Partial Data Only?
- iOS devices may not sync immediately after setup
- Historical data (older than 7 days) may not sync
- Web usage data is only available from Safari on iOS

## 📝 Data Schema

iOS data includes these additional fields:
- `device_name`: "📱 iPhone 15 Pro", "📱 iPad Pro 12.9""
- `device_model`: "iPhone16,1", "iPad8,11"
- `device_id`: Unique identifier for each device
- `url`: Website URLs for Safari usage
- `gmt_offset`: Timezone offset for the device

## 🚀 Ready to Use!

Your Python implementation is already set up to handle iOS data. Once you enable Screen Time sync, your existing commands will automatically include iOS device usage:

```bash
# Sync all devices (Mac + iOS)
python -m src.main sync --days 7

# Export data from all devices
python -m src.main export --days 30

# Analyze apps across all devices
python -m src.main analyze-apps --days 7
```

The `--mac-only` flag can be used to exclude iOS devices if needed.