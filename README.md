# ScreenTime2Notion

A Python tool that reads macOS Screen Time data from the local knowledgeC.db SQLite database, processes app usage sessions, maps them to custom categories, and syncs them into a Notion database for weekly usage tracking.

> 📊 **Weekly Usage Tracking** - Creates one row per app per week for clean, organized usage insights
> 
> 🔒 **Manual Entry Protection** - Respects and preserves any manual entries you add to your Notion database

## Features

- 🔍 **Direct Screen Time Access**: Reads data directly from macOS knowledgeC.db database
- 📊 **Weekly Aggregation**: Creates one row per app per week (Monday-Sunday) for organized tracking
- 🏷️ **Custom Categories**: Maps apps to customizable categories (Work, Learn, Procrastinate, etc.)
- 🔒 **Manual Entry Protection**: Preserves manually added entries in your Notion database
- 😴 **Sleep Detection**: Automatically detects and tracks sleep sessions
- 🌐 **App vs Website Detection**: Distinguishes between native apps and web-based usage
- 🔄 **Smart Notion Sync**: Updates existing entries, creates new ones, skips manual entries
- 📈 **CSV Export**: Export usage data to CSV for analysis
- ⚙️ **CLI Interface**: Easy-to-use command-line interface with multiple commands
- 📅 **Date Range Support**: Process specific date ranges
- 🔧 **Configurable**: JSON-based category configuration
- 🧪 **Test Mode**: Generate realistic test data for development

## Installation

### Option 1: Install from PyPI (Recommended)
```bash
pip install screentime2notion
```

### Option 2: Install from Source
1. Clone the repository:
```bash
git clone https://github.com/yourusername/screentime2notion.git
cd screentime2notion
```

2. Install the package:
```bash
pip install -e .
```

### Requirements
- **macOS** with Screen Time enabled
- **Python 3.8+**
- **Full Disk Access** permission for Terminal (see Setup section)

### Important Notes
- **macOS Only**: This tool reads from the local `knowledgeC.db` which only contains Screen Time data for the current Mac
- **No iOS/iPadOS Data**: iPhone and iPad usage data is not accessible through macOS - they use separate Screen Time databases
- **Per-Device Tracking**: Each Mac needs to run the tool separately to track its usage

## Setup

### 1. macOS Permissions

**Grant Full Disk Access to Terminal:**
1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Full Disk Access** from the left sidebar
3. Click the lock icon and enter your password
4. Click **+** and add your **Terminal** app
5. Restart Terminal

### 2. Notion Setup

1. **Create a Notion Integration:**
   - Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Click "**+ New integration**"
   - Name it "ScreenTime2Notion" and select your workspace
   - Copy the **Internal Integration Token**

2. **Create a Notion Database:**
   - Create a new page in Notion
   - Add a database (table) to the page
   - Copy the **database ID** from the URL: `notion.so/.../{database_id}?v=...`

3. **Share Database with Integration:**
   - In your database page, click **Share** (top right)
   - Click **Invite** and select your integration
   - Give it **Edit** access

### 3. Configuration

**Option 1: Interactive Setup (Recommended)**
```bash
screentime2notion configure
```

**Option 2: Manual Setup**
Create a `.env` file in your project directory:
```bash
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## Quick Start

### 1. First Time Setup
```bash
# Configure credentials
screentime2notion configure

# Set up database schema and sync last 7 days
screentime2notion sync --setup-schema --days 7
```

### 2. Regular Usage
```bash
# Weekly sync (recommended)
screentime2notion sync --days 7
```

## Commands

### `sync` - Sync Screen Time data to Notion
```bash
# Basic sync (last 7 days)
screentime2notion sync

# Custom date range
screentime2notion sync --days 14

# Setup database schema on first run
screentime2notion sync --setup-schema

# Preview without syncing
screentime2notion sync --dry-run

# Mac only (exclude iOS devices)
screentime2notion sync --mac-only
```

### `export` - Export data to CSV
```bash
# Export weekly usage data
screentime2notion export --days 30 --output screentime.csv

# Export category summary
screentime2notion export --category-summary --output categories.csv
```

### `apps` - Manage app categories
```bash
# List all apps with categories
screentime2notion apps

# Show apps that need categorization
screentime2notion apps --uncategorized

# Add custom category mapping
screentime2notion categorize "My App" "Work"
```

### `devices` - Show available devices
```bash
# Show all devices with Screen Time data
screentime2notion devices
```

### `debug-screentime` - Debug Screen Time access
```bash
# Debug Screen Time database access
screentime2notion debug-screentime --days 7 --show-raw
```

### `test` - Test with sample data
```bash
# Generate test data (dry run)
screentime2notion test --days 7

# Generate and sync test data
screentime2notion test --days 7 --sync
```

### `info` - System information
```bash
screentime2notion info
```

### `clear-notion` - Clear Notion database
```bash
screentime2notion clear-notion
```

## Configuration

### Category Mapping

Categories are defined in `config/categories.json`. You can customize:

- **App names**: Direct app name matching
- **Bundle patterns**: Regex patterns for bundle identifiers
- **Colors**: Notion select colors for categories
- **Filtering rules**: Minimum duration, ignored apps

Example category configuration:
```json
{
  "categories": {
    "Work": {
      "color": "blue",
      "apps": ["Notion", "Visual Studio Code", "Terminal"],
      "bundle_patterns": ["com.microsoft.*", "com.notion.*"]
    }
  }
}
```

### Available Categories

- 🔵 **Work**: Work-related apps (Notion, VS Code, Office)
- 🟡 **Learn**: Learning apps (Anki, Coursera, Books)
- 🟢 **Socialize**: Messaging and video calls (Slack, Zoom, Messages)
- 🔴 **Procrastinate**: Entertainment and social media (YouTube, Netflix, Twitter)
- 🟣 **Exercise**: Fitness apps
- 🟠 **Family**: Family-related apps (Messages, Photos)
- ⚫ **Other**: Uncategorized apps
- 🟪 **Sleeping**: Sleep sessions (automatically detected)

## How It Works

### Data Processing Pipeline

1. **Raw Data Extraction**: Reads from macOS knowledgeC.db SQLite database
2. **Session Processing**: Merges overlapping sessions, filters noise (< 5s sessions)
3. **Sleep Detection**: Identifies sleep periods from display backlight data
4. **App vs Website Detection**: Distinguishes native apps from web usage
5. **Categorization**: Maps apps to custom categories using JSON config
6. **Weekly Aggregation**: Groups usage into weekly totals per app
7. **Smart Sync**: Updates Notion while preserving manual entries

### Notion Database Schema

The tool automatically sets up these Notion database properties:

| Property | Type | Description |
|----------|------|-------------|
| **App Name** | Title | Display name of the application |
| **App ID** | Text | Bundle identifier (e.g., com.apple.Safari) |
| **Date** | Date | Week start date (Monday) |
| **Category** | Select | App category (Work, Learn, etc.) |
| **Type** | Select | App or Website |
| **Domain** | Text | Website domain (for web usage) |
| **Device** | Text | Device name with emoji (💻 Mac, 📱 iPhone) |
| **Minutes** | Number | Total usage in minutes for the week |
| **Hours** | Number | Total usage in hours for the week |
| **Sessions** | Number | Number of usage sessions during the week |
| **Last Updated** | Date | When the record was last synced |

### Manual Entry Protection

The tool **automatically protects** any manual entries you add to your Notion database:
- Entries without an App ID are considered manual
- Manual entries are never updated or deleted
- Shows "🔒 Protecting manual entry" messages during sync

## Requirements

- macOS with Screen Time enabled
- Python 3.8+
- Notion account and API key
- Screen Time permissions (may require Full Disk Access in Privacy settings)

## Troubleshooting

### Permission Issues
If you get permission errors accessing knowledgeC.db:
1. Grant Full Disk Access to Terminal in System Preferences > Privacy
2. Or run the script from an app with Full Disk Access

### No Data Found
- Ensure Screen Time is enabled in System Preferences
- Check that you have recent app usage
- Verify the knowledgeC.db file exists at `~/Library/Application Support/Knowledge/knowledgeC.db`

### Notion Connection Issues
- Verify your API key is correct
- Ensure the database is shared with your integration
- Check the database ID is correct

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.