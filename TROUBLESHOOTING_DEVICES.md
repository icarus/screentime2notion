# Device Recognition Troubleshooting

## Problem: iOS devices showing as "Mac" or not appearing

### Root Cause
Screen Time data sharing between your Apple devices is not properly enabled, even though device sync is working for other data types.

### Solution Steps

1. **Enable Screen Time sharing on iOS devices:**
   - Open **Settings** → **Screen Time**
   - Tap **Share Across Devices** → Turn **ON**
   - Repeat on ALL iOS devices

2. **Enable Screen Time sharing on Mac:**
   - Open **System Settings** → **Screen Time**
   - Click **Options**
   - Turn **ON** "Share Across Devices"

3. **Force sync refresh (if already enabled):**
   - Turn OFF "Share Across Devices" on all devices
   - Wait 30 seconds
   - Turn ON "Share Across Devices" on all devices

4. **Wait for sync:**
   - Initial sync can take 6-24 hours
   - Force restart all devices to speed up sync

### Verify it's working

```bash
# Check if iOS devices are syncing Screen Time data
python -m src.main check-ios

# List all available devices
python -m src.main devices

# Debug actual Screen Time data
python -m src.main debug-screentime --days 7
```

### Expected vs Current Behavior

**Current (broken):**
```
📱 Available Devices:
💻 Mac (Mac) - 628 sessions
```

**Expected (fixed):**
```
📱 Available Devices:
💻 iMac14,1 (iMac14,1) - 300 sessions
📱 iPhone 15 Pro Max (iPhone16,2) - 150 sessions  
📱 iPad Pro 12.9" (iPad8,11) - 100 sessions
```

### Why this happens

Apple's Screen Time database (`knowledgeC.db`) syncs device information separately from usage data:
- ✅ Device info syncs automatically (bluetooth, connectivity)
- ❌ Screen Time usage requires explicit permission via "Share Across Devices"

### Alternative: Mac-only mode

If you only want Mac data and don't need iOS sync:

```bash
# Sync only Mac data (ignores iOS devices)
python -m src.main sync --mac-only
```