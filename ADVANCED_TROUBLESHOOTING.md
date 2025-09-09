# Advanced iOS Screen Time Troubleshooting

## Current Diagnosis

Based on deep database analysis, here's what's happening:

### ✅ **What's Working**
- Device sync is working (9 iOS devices registered)
- iPhone16,2 synced as recently as today (2025-09-09)
- Other data types ARE syncing from iOS (bluetooth, notifications)
- Local Mac Screen Time works perfectly (10,362 sessions, 57.5h)

### ❌ **What's NOT Working**
- **Zero** Screen Time usage records from ANY iOS device
- Even your iMac14,1 shows no usage data despite being registered
- Only "local Mac" data (without device ID) contains usage records

## Root Cause: Screen Time Usage vs Device Sync

Apple separates two different types of sync:
1. **Device Information Sync** ✅ (Working - this is why devices appear in ZSYNCPEER)
2. **Screen Time Usage Sync** ❌ (Broken - this is why no `/app/usage` records exist)

## Advanced Solutions

### 1. **Privacy & Security Settings** (Most Likely Fix)

**Mac:**
```
System Settings → Privacy & Security → Analytics & Improvements
→ Share Mac Analytics: ON
→ Improve Siri & Dictation: ON

System Settings → Apple ID → Media & Purchases
→ Make sure you're signed in with the same Apple ID
```

**iOS (Each Device):**
```
Settings → Privacy & Security → Analytics & Improvements
→ Share iPhone Analytics: ON
→ Share iPhone & Watch Analytics: ON (if you have Apple Watch)

Settings → Screen Time → Share Across Devices
→ Turn OFF → Wait 30 seconds → Turn ON
```

### 2. **Reset Screen Time Sync**

**Complete Reset Method:**
```bash
# 1. On ALL devices: Turn OFF "Share Across Devices"
# 2. Sign out of iCloud completely on ONE iOS device
# 3. Wait 5 minutes
# 4. Sign back into iCloud
# 5. Re-enable Screen Time sharing on ALL devices
# 6. Wait 24-48 hours
```

### 3. **Check iCloud Storage & Sync**

**Verify iCloud has space and Screen Time is enabled:**
```
iOS: Settings → [Your Name] → iCloud
→ Make sure Screen Time is toggled ON
→ Check available iCloud storage (needs >100MB free)

Mac: System Settings → Apple ID → iCloud
→ Make sure you're signed into the SAME Apple ID
→ Screen Time sync should be enabled
```

### 4. **Family Sharing Configuration**

If you're using Family Sharing, Screen Time might be managed at family level:

```
iOS: Settings → [Your Name] → Family Sharing → Screen Time
→ Make sure YOUR device isn't being managed by family organizer
→ If it is, ask family organizer to enable sharing for your device

Mac: System Settings → Family → Screen Time
→ Verify your Apple ID has permission to share its own data
```

### 5. **Force Sync with Activity Monitor**

**Terminal Commands to Force Sync:**
```bash
# Kill and restart Screen Time processes
sudo pkill -f "ScreenTimeAgent"
sudo pkill -f "UsageTrackingAgent"

# Force iCloud sync
killall bird
killall cloudd

# Restart and check
python -m src.main check-ios
```

## Verification Steps

After trying fixes, check progress:

```bash
# 1. Check device registration (should show recent last_seen dates)
python -c "
import sqlite3, os
db_path = os.path.expanduser('~/Library/Application Support/Knowledge/knowledgeC.db')
with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as conn:
    cursor = conn.execute('SELECT ZMODEL, datetime(ZLASTSEENDATE + 978307200, \"unixepoch\") FROM ZSYNCPEER WHERE ZMODEL LIKE \"iPhone%\" ORDER BY ZLASTSEENDATE DESC LIMIT 3')
    for model, last_seen in cursor.fetchall():
        print(f'{model}: {last_seen}')
"

# 2. Check for ANY iOS usage data
python -m src.main check-ios

# 3. Test the fix
python -m src.main devices
```

## Expected Timeline

- **Device registration**: Immediate (already working)  
- **Basic data sync**: 1-6 hours (bluetooth, etc. - already working)
- **Screen Time usage sync**: 6-24 hours (this is what's missing)
- **Full historical sync**: 2-7 days

## Alternative: Extract iOS Data Directly

If sync continues to fail, you can extract iOS Screen Time data directly:

**iPhone/iPad:**
1. Settings → Privacy & Security → Analytics → Analytics Data
2. Look for files named like "ScreenTimeAgent-2025-xx-xx"
3. These contain your iOS usage data in XML format

**Python script to parse iOS analytics:**
```bash
# Create iOS data extractor if needed
python -m src.main create-ios-extractor
```

## Status Check

Your current status:
- ✅ Device connectivity: Perfect
- ✅ Mac Screen Time: Working (10K+ sessions)
- ❌ iOS Screen Time sync: Completely missing
- 🔄 Recommendation: Start with Privacy & Security settings reset

The fact that your iPhone16,2 synced TODAY means the connection works - it's just a settings/permission issue blocking Screen Time specifically.