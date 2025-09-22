#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title ScreenTime Sync
# @raycast.mode fullOutput
# @raycast.packageName ScreenTime2Notion

# Optional parameters:
# @raycast.icon 📱
# @raycast.description Manually sync Screen Time data to Notion

cd /Users/felipe/code/icarus/screentime2notion

echo "🚀 Starting ScreenTime2Notion sync..."
./venv/bin/python -m src.main sync --days 7

echo "✅ Sync completed!"
