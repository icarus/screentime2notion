# ScreenTime2Notion

macOS saves Screen Time data for all your iCloud enabled devices inside a local SQLite file stored at `~/Library/Application Support/Knowledge/knowledgeC.db`. This tool reads that data and syncs it to a Notion database with custom categories and weekly aggregation.

Note: Only works on macOS. iOS data sync may be inconsistent depending on your iCloud settings.

## Quick Start

```bash
# Install
pip install screentime2notion

# Configure Notion credentials
screentime2notion configure

# First sync with database setup
screentime2notion sync --setup-schema --days 7
```

## Features

- Reads Screen Time data directly from knowledgeC.db
- Weekly aggregation (one row per app per week)
- Custom app categorization via JSON config
- Protects manual entries in Notion
- Sleep session detection
- Multi-device support (when iOS data syncs)
- CSV export functionality

## Setup

### 1. macOS Permissions
1. System Preferences > Security & Privacy > Privacy
2. Select "Full Disk Access"
3. Add Terminal app
4. Restart Terminal

### 2. Notion Setup
1. Create integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create a new database in Notion
3. Share database with your integration
4. Copy API key and database ID

![How to get the database ID](images/url.png)

### 3. Configure
```bash
screentime2notion configure
```

Or create `.env` file:
```bash
NOTION_API_KEY=your_api_key_here
NOTION_DATABASE_ID=your_database_id_here
```

## Usage

```bash
# Basic sync (last 7 days)
screentime2notion sync

# Export to CSV
screentime2notion export --output usage.csv

# Show available devices
screentime2notion devices

# List apps by category
screentime2notion apps

# Add custom category mapping
screentime2notion categorize "App Name" "Work"
```

## Configuration

Categories are defined in `config/categories.json`:

```json
{
  "categories": {
    "Work": {
      "color": "blue",
      "apps": ["Visual Studio Code", "Terminal", "Notion"],
      "bundle_patterns": ["com.microsoft.*", "com.apple.dt.Xcode"]
    }
  }
}
```

## Data Schema

The Notion database includes these properties:

| Property | Type | Description |
|----------|------|-------------|
| App Name | Title | Application display name |
| App ID | Text | Bundle identifier |
| Date | Date | Week start date (Monday) |
| Category | Select | Custom category |
| Device | Text | Device name |
| Hours | Number | Usage hours for the week |
| Sessions | Number | Number of sessions |

![Example 1](images/chart.png)
![Example 2](images/data.png)

## Development

```bash
git clone https://github.com/yourusername/screentime2notion.git
cd screentime2notion
pip install -e .
```

## License

MIT
