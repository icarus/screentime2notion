#!/bin/bash

# Setup automatic Screen Time sync to Notion
PROJECT_DIR="/Users/felipe/code/icarus/screentime2notion"

echo "🔧 Setting up automatic Screen Time → Notion sync..."

# Add cron job for daily sync at 9 PM
(crontab -l 2>/dev/null; echo "0 21 * * * cd $PROJECT_DIR && python -m src.main sync --days 7 >> sync.log 2>&1") | crontab -

echo "✅ Cron job added: Daily sync at 9 PM"
echo "📁 Working directory: $PROJECT_DIR"
echo "📝 Logs will be saved to: $PROJECT_DIR/sync.log"
echo ""
echo "🔍 To check if it's working:"
echo "  tail -f $PROJECT_DIR/sync.log"
echo ""
echo "📅 To view your cron jobs:"
echo "  crontab -l"
echo ""
echo "🗑️  To remove the cron job later:"
echo "  crontab -e  # then delete the line"