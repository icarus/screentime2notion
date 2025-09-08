#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import click
from dotenv import load_dotenv
import pandas as pd

from .screentime_reader import ScreenTimeReader
from .data_processor import DataProcessor
from .category_mapper import CategoryMapper
from .notion_sync import NotionSyncer
from .test_data_generator import TestDataGenerator
from .sleep_detector import SleepDetector

# Load environment variables
load_dotenv()

@click.group()
@click.version_option("0.1.0")
def cli():
    """ScreenTime2Notion - Sync your Screen Time data to Notion with custom categories."""
    pass

@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to sync (default: 7)')
@click.option('--batch-size', default=10, help='Batch size for Notion sync (default: 10)')
@click.option('--setup-schema', is_flag=True, help='Set up Notion database schema')
@click.option('--dry-run', is_flag=True, help='Process data but don\'t sync to Notion')
@click.option('--mac-only', is_flag=True, help='Only include Mac data, exclude iOS devices')
def sync(days, batch_size, setup_schema, dry_run, mac_only):
    """Sync Screen Time data to Notion database."""
    
    # Check for required environment variables
    api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not api_key:
        click.echo("❌ NOTION_API_KEY not found in environment variables")
        click.echo("Please set up your .env file or run 'screentime2notion configure'")
        return
    
    if not database_id:
        click.echo("❌ NOTION_DATABASE_ID not found in environment variables")
        click.echo("Please set up your .env file or run 'screentime2notion configure'")
        return
    
    try:
        # Initialize components
        click.echo("🔍 Reading Screen Time data...")
        reader = ScreenTimeReader()
        processor = DataProcessor()
        mapper = CategoryMapper()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        click.echo(f"📅 Processing data from {start_date.date()} to {end_date.date()}")
        
        # Read and process data (include all devices by default unless --mac-only is specified)
        raw_data = reader.get_app_usage_data(start_date, end_date, include_all_devices=not mac_only)
        if raw_data.empty:
            click.echo("⚠️ No Screen Time data found for the specified date range")
            return
        
        click.echo(f"📊 Found {len(raw_data)} raw usage sessions")
        
        # Process sessions
        processed_data = processor.process_usage_sessions(raw_data)
        click.echo(f"🔄 Processed into {len(processed_data)} sessions")
        
        # Categorize apps
        categorized_data = mapper.categorize_dataframe(processed_data)
        click.echo(f"🏷️ Categorized {len(categorized_data)} sessions")
        
        # Detect sleep sessions
        sleep_detector = SleepDetector(reader.db_path)
        sleep_data = sleep_detector.get_sleep_sessions(start_date, end_date)
        
        if not sleep_data.empty:
            click.echo(f"😴 Found {len(sleep_data)} sleep sessions")
            # Combine app usage data with sleep data
            categorized_data = pd.concat([categorized_data, sleep_data], ignore_index=True)
        else:
            click.echo("😴 No sleep sessions detected")
        
        # Aggregate weekly usage (one row per app per week)
        weekly_usage = processor.aggregate_weekly_usage(categorized_data)
        
        if weekly_usage.empty:
            click.echo("⚠️ No data to sync after processing")
            return
        
        click.echo(f"📈 Prepared {len(weekly_usage)} weekly usage records")
        
        # Display summary
        summary = processor.get_usage_summary(categorized_data)
        click.echo("\n📋 Summary:")
        click.echo(f"  • Total apps: {summary['total_apps']}")
        click.echo(f"  • Total sessions: {summary['total_sessions']}")
        click.echo(f"  • Total usage: {summary['total_hours']} hours")
        click.echo(f"  • Average daily: {summary['avg_daily_usage']} hours")
        
        # Show top categories
        category_summary = mapper.get_category_summary(categorized_data)
        if not category_summary.empty:
            click.echo("\n🎯 Top Categories:")
            for _, row in category_summary.head(5).iterrows():
                click.echo(f"  • {row['category']}: {row['duration_hours']}h ({row['percentage']}%)")
        
        if dry_run:
            click.echo("\n🔍 Dry run completed - no data synced to Notion")
            return
        
        # Initialize Notion syncer
        click.echo("\n🔗 Connecting to Notion...")
        syncer = NotionSyncer(api_key, database_id)
        
        # Set up schema if requested
        if setup_schema:
            click.echo("⚙️ Setting up database schema...")
            syncer.setup_database_schema()
        
        # Sync data
        click.echo("🚀 Syncing to Notion...")
        results = syncer.sync_usage_data(weekly_usage, batch_size)
        
        click.echo(f"\n✅ Sync completed:")
        click.echo(f"  • Synced: {results['synced']} records")
        click.echo(f"  • Errors: {results['errors']} records")
        click.echo(f"  • Skipped: {results['skipped']} records")
        
        # Get database info
        db_info = syncer.get_database_info()
        if 'url' in db_info:
            click.echo(f"  • Database: {db_info['url']}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)

@cli.command()
@click.option('--output', '-o', default='screentime_export.csv', help='Output filename')
@click.option('--days', '-d', default=30, help='Number of days to export (default: 30)')
@click.option('--category-summary', is_flag=True, help='Export category summary instead of raw data')
def export(output, days, category_summary):
    """Export Screen Time data to CSV."""
    
    try:
        click.echo("🔍 Reading Screen Time data...")
        reader = ScreenTimeReader()
        processor = DataProcessor()
        mapper = CategoryMapper()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Read and process data
        raw_data = reader.get_app_usage_data(start_date, end_date)
        if raw_data.empty:
            click.echo("⚠️ No Screen Time data found")
            return
        
        processed_data = processor.process_usage_sessions(raw_data)
        categorized_data = mapper.categorize_dataframe(processed_data)
        
        if category_summary:
            # Export category summary
            summary_data = mapper.get_category_summary(categorized_data)
            summary_data.to_csv(output, index=False)
            click.echo(f"📊 Category summary exported to {output}")
        else:
            # Export detailed weekly usage
            weekly_usage = processor.aggregate_weekly_usage(categorized_data)
            weekly_usage.to_csv(output, index=False)
            click.echo(f"📈 Weekly usage data exported to {output}")
        
        click.echo(f"✅ Export completed: {output}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)

@cli.command()
def configure():
    """Interactive configuration setup."""
    
    click.echo("🔧 ScreenTime2Notion Configuration Setup")
    click.echo("=" * 50)
    
    # Get Notion API key
    api_key = click.prompt("Enter your Notion API key", hide_input=True)
    
    # Get Notion database ID
    database_id = click.prompt("Enter your Notion database ID")
    
    # Create .env file
    env_path = Path(".env")
    with open(env_path, "w") as f:
        f.write(f"NOTION_API_KEY={api_key}\n")
        f.write(f"NOTION_DATABASE_ID={database_id}\n")
    
    click.echo(f"✅ Configuration saved to {env_path.absolute()}")
    
    # Test connection
    try:
        click.echo("🔗 Testing Notion connection...")
        syncer = NotionSyncer(api_key, database_id)
        db_info = syncer.get_database_info()
        
        if 'error' not in db_info:
            click.echo("✅ Connection successful!")
            click.echo(f"  • Database: {db_info.get('title', 'Untitled')}")
            click.echo(f"  • URL: {db_info.get('url', 'N/A')}")
            
            # Offer to set up schema
            if click.confirm("Would you like to set up the database schema now?"):
                syncer.setup_database_schema()
                click.echo("✅ Database schema configured")
        else:
            click.echo(f"❌ Connection failed: {db_info['error']}")
    
    except Exception as e:
        click.echo(f"❌ Connection test failed: {e}")

@cli.command()
@click.option('--uncategorized', is_flag=True, help='Show uncategorized apps only')
def apps():
    """List available apps and their categories."""
    
    try:
        reader = ScreenTimeReader()
        mapper = CategoryMapper()
        
        # Get recent data for app analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        raw_data = reader.get_app_usage_data(start_date, end_date)
        if raw_data.empty:
            click.echo("⚠️ No Screen Time data found")
            return
        
        processor = DataProcessor()
        processed_data = processor.process_usage_sessions(raw_data)
        categorized_data = mapper.categorize_dataframe(processed_data)
        
        if uncategorized:
            # Show only uncategorized apps
            uncategorized_apps = mapper.get_uncategorized_apps(processed_data)
            click.echo(f"🏷️ Uncategorized apps ({len(uncategorized_apps)}):")
            for app in sorted(uncategorized_apps):
                click.echo(f"  • {app}")
        else:
            # Show all apps with categories
            app_categories = categorized_data.groupby(['app_display_name', 'category']).agg({
                'duration_minutes': 'sum'
            }).reset_index().sort_values('duration_minutes', ascending=False)
            
            click.echo(f"📱 Apps by category ({len(app_categories)}):")
            
            for category in mapper.get_available_categories():
                category_apps = app_categories[app_categories['category'] == category]
                if not category_apps.empty:
                    click.echo(f"\n🏷️ {category}:")
                    for _, row in category_apps.head(10).iterrows():
                        duration_h = row['duration_minutes'] / 60
                        click.echo(f"  • {row['app_display_name']}: {duration_h:.1f}h")
    
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)

@cli.command()
@click.argument('app_name')
@click.argument('category')
def categorize(app_name, category):
    """Add custom app-to-category mapping."""
    
    try:
        mapper = CategoryMapper()
        
        if mapper.add_custom_mapping(app_name, category):
            click.echo(f"✅ Mapped '{app_name}' to category '{category}'")
        else:
            click.echo(f"❌ Failed to map '{app_name}' to category '{category}'")
    
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
def info():
    """Show system and configuration info."""
    
    click.echo("ℹ️ ScreenTime2Notion Information")
    click.echo("=" * 40)
    
    # Check Screen Time database
    try:
        reader = ScreenTimeReader()
        click.echo(f"✅ Screen Time database found: {reader.db_path}")
        
        # Get sample data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        sample_data = reader.get_app_usage_data(start_date, end_date)
        click.echo(f"📊 Recent sessions (24h): {len(sample_data)}")
        
    except Exception as e:
        click.echo(f"❌ Screen Time database error: {e}")
    
    # Check configuration
    api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if api_key and database_id:
        click.echo("✅ Notion configuration found")
        try:
            syncer = NotionSyncer(api_key, database_id)
            db_info = syncer.get_database_info()
            if 'error' not in db_info:
                click.echo(f"✅ Notion database accessible: {db_info.get('title', 'Untitled')}")
        except:
            click.echo("❌ Notion connection failed")
    else:
        click.echo("⚠️ Notion configuration missing - run 'screentime2notion configure'")
    
    # Check categories config
    try:
        mapper = CategoryMapper()
        categories = mapper.get_available_categories()
        click.echo(f"✅ Categories loaded: {len(categories)} categories")
    except Exception as e:
        click.echo(f"❌ Categories config error: {e}")

@cli.command()
@click.option('--days', '-d', default=3, help='Number of days to analyze')
@click.option('--show-detection', is_flag=True, help='Show app vs website detection details')
def analyze_apps(days, show_detection):
    """Analyze apps vs websites and show detection results."""
    
    try:
        click.echo("🔍 Analyzing Apps vs Websites")
        click.echo("=" * 50)
        
        reader = ScreenTimeReader()
        processor = DataProcessor()
        mapper = CategoryMapper()
        
        # Get recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        raw_data = reader.get_app_usage_data(start_date, end_date)
        if raw_data.empty:
            click.echo("No data found")
            return
        
        processed_data = processor.process_usage_sessions(raw_data)
        categorized_data = mapper.categorize_dataframe(processed_data)
        
        click.echo(f"📊 Found {len(categorized_data)} sessions from {len(categorized_data['app_name'].unique())} unique apps")
        
        # Analyze each unique app
        unique_apps = categorized_data.groupby(['app_name', 'app_display_name', 'category']).agg({
            'duration_minutes': 'sum'
        }).reset_index().sort_values('duration_minutes', ascending=False)
        
        # Create a simple detection function here to avoid NotionSyncer initialization
        def detect_app_type_and_domain(app_name: str, display_name: str):
            import os
            
            # Get browser apps from env
            browser_apps = os.getenv('BROWSER_APPS', '').split(',') if os.getenv('BROWSER_APPS') else []
            
            website_indicators = [
                '.webClipWrapper',
                'com.apple.WebKit.WebContent',
                'com.google.Chrome.app.',
                'com.microsoft.edgemac.app.',
                'org.mozilla.firefox.app.',
            ]
            
            for indicator in website_indicators:
                if indicator in app_name:
                    domain = extract_domain(app_name, display_name)
                    return "Website", domain
            
            # Check if it's a browser from env config
            if app_name in browser_apps:
                return "Website", "web browsing"
            
            return "App", ""
        
        def extract_domain(app_name: str, display_name: str):
            import re
            domain_patterns = [
                r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})',
                r'\.([a-zA-Z0-9-]+\.[a-zA-Z]{2,})\.',
            ]
            
            for pattern in domain_patterns:
                matches = re.findall(pattern, app_name)
                if matches:
                    return matches[0]
            
            for pattern in domain_patterns:
                matches = re.findall(pattern, display_name)
                if matches:
                    return matches[0]
            
            return ""
        
        click.echo(f"\n📱 App Type Analysis:")
        click.echo("-" * 80)
        
        apps_count = 0
        websites_count = 0
        
        for _, row in unique_apps.iterrows():
            app_type, domain = detect_app_type_and_domain(row['app_name'], row['app_display_name'])
            duration_h = row['duration_minutes'] / 60
            
            type_icon = "🌐" if app_type == "Website" else "📱"
            domain_info = f" (domain: {domain})" if domain else ""
            
            click.echo(f"  {type_icon} {row['app_display_name']:<25} → {row['category']:<15} ({duration_h:.1f}h) [{app_type}]{domain_info}")
            
            if show_detection:
                click.echo(f"      Bundle ID: {row['app_name']}")
            
            if app_type == "Website":
                websites_count += 1
            else:
                apps_count += 1
        
        click.echo(f"\n📈 Detection Summary:")
        click.echo(f"  • Apps: {apps_count}")
        click.echo(f"  • Websites: {websites_count}")
        click.echo(f"  • Total: {apps_count + websites_count}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to read from Screen Time database')
@click.option('--show-raw', is_flag=True, help='Show raw database entries for debugging')
def debug_screentime(days, show_raw):
    """Debug Screen Time database access and log all found apps."""
    
    click.echo("🔍 ScreenTime Debug Mode")
    click.echo("=" * 50)
    
    try:
        # Try different database locations
        possible_paths = [
            os.path.expanduser("~/Library/Application Support/Knowledge/knowledgeC.db"),
            "/private/var/folders/*/*/C/com.apple.knowledge-agent/local/knowledgeC.db",
            "/var/folders/*/*/C/com.apple.knowledge-agent/local/knowledgeC.db"
        ]
        
        working_path = None
        for path in possible_paths:
            if '*' in path:
                # Use glob to find the actual path
                import glob
                matches = glob.glob(path)
                for match in matches:
                    if os.path.exists(match):
                        working_path = match
                        break
            elif os.path.exists(path):
                working_path = path
                break
        
        if working_path:
            click.echo(f"📁 Found database at: {working_path}")
        else:
            click.echo("❌ Could not find knowledgeC.db - trying default location anyway")
            working_path = None
        
        # Initialize reader
        reader = ScreenTimeReader(working_path)
        processor = DataProcessor()
        mapper = CategoryMapper()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        click.echo(f"📅 Attempting to read data from {start_date.date()} to {end_date.date()}")
        
        # Try to read data
        raw_data = reader.get_app_usage_data(start_date, end_date)
        
        if raw_data.empty:
            click.echo("⚠️ No Screen Time data found - possible causes:")
            click.echo("  • Screen Time not enabled")
            click.echo("  • No recent app usage")
            click.echo("  • Permission denied (need Full Disk Access)")
            click.echo("  • Wrong database location")
            return
        
        click.echo(f"🎉 Successfully read {len(raw_data)} raw usage sessions!")
        
        if show_raw:
            click.echo("\n📊 Raw Database Entries (first 20):")
            click.echo("-" * 80)
            for _, row in raw_data.head(20).iterrows():
                click.echo(f"  {row['app_name']:<40} | {row['app_display_name']:<25} | {row['duration_minutes']:.1f}min")
        
        # Process the data
        processed_data = processor.process_usage_sessions(raw_data)
        categorized_data = mapper.categorize_dataframe(processed_data)
        
        # Show all unique apps found
        click.echo(f"\n📱 All Apps Found in Your Screen Time Data:")
        click.echo("-" * 70)
        
        app_summary = categorized_data.groupby(['app_name', 'app_display_name', 'category']).agg({
            'duration_minutes': 'sum'
        }).reset_index().sort_values('duration_minutes', ascending=False)
        
        for _, row in app_summary.iterrows():
            duration_h = row['duration_minutes'] / 60
            bundle_id = row['app_name'] if row['app_name'] != row['app_display_name'] else ""
            click.echo(f"  🏷️  {row['app_display_name']:<25} → {row['category']:<15} ({duration_h:.1f}h)")
            if bundle_id and len(bundle_id) > 30:
                click.echo(f"      Bundle: {bundle_id}")
        
        # Show category breakdown
        category_summary = mapper.get_category_summary(categorized_data)
        if not category_summary.empty:
            click.echo(f"\n📊 Your Usage by Category:")
            click.echo("-" * 40)
            for _, row in category_summary.iterrows():
                click.echo(f"  {row['category']:<15}: {row['duration_hours']:.1f}h ({row['percentage']:.1f}%) - {row['unique_apps']} apps")
        
        # Show uncategorized apps that need manual categorization
        uncategorized_apps = mapper.get_uncategorized_apps(processed_data)
        if uncategorized_apps:
            click.echo(f"\n🏷️ Uncategorized Apps (need manual categorization):")
            click.echo("-" * 50)
            for app in uncategorized_apps:
                click.echo(f"  ❓ {app}")
                click.echo(f"     → Run: screentime2notion categorize \"{app}\" \"<category>\"")
        
        # Overall summary
        summary = processor.get_usage_summary(categorized_data)
        click.echo(f"\n📋 Your Screen Time Summary:")
        click.echo(f"  • Total apps: {summary['total_apps']}")
        click.echo(f"  • Total sessions: {summary['total_sessions']}")
        click.echo(f"  • Total usage: {summary['total_hours']} hours")
        click.echo(f"  • Average daily: {summary['avg_daily_usage']} hours")
        
        click.echo(f"\n💡 Next steps:")
        click.echo(f"  • Categorize uncategorized apps using 'screentime2notion categorize'")
        click.echo(f"  • Run 'screentime2notion sync' to upload to Notion")
        
    except Exception as e:
        click.echo(f"❌ Error reading Screen Time data: {e}")
        click.echo(f"\n🔧 Troubleshooting:")
        click.echo(f"  • Enable Screen Time in System Preferences")
        click.echo(f"  • Grant Full Disk Access to Terminal in Privacy & Security settings")
        click.echo(f"  • Make sure you have recent app usage data")
        import traceback
        traceback.print_exc()

@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to generate test data for (default: 7)')
@click.option('--sync', is_flag=True, help='Actually sync to Notion (not just dry run)')
def test(days, sync):
    """Test the application with generated sample data and detailed logging."""
    
    click.echo("🧪 ScreenTime2Notion Test Mode")
    click.echo("=" * 50)
    
    # Check for Notion credentials
    api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not api_key or not database_id:
        click.echo("⚠️ Notion credentials not found - running in demo mode only")
        sync = False
    
    try:
        # Generate test data
        click.echo(f"🎲 Generating test data for {days} days...")
        generator = TestDataGenerator()
        raw_data = generator.generate_realistic_usage_data(days)
        
        if raw_data.empty:
            click.echo("❌ No test data generated")
            return
        
        # Initialize processors
        processor = DataProcessor()
        mapper = CategoryMapper()
        
        # Process data
        click.echo("\n📊 Processing usage sessions...")
        processed_data = processor.process_usage_sessions(raw_data)
        click.echo(f"✓ Processed {len(processed_data)} sessions")
        
        # Categorize and log results
        click.echo("\n🏷️ Categorizing applications...")
        categorized_data = mapper.categorize_dataframe(processed_data)
        
        # Log all apps and their categories
        click.echo("\n📱 App Categorization Results:")
        click.echo("-" * 60)
        
        app_categories = categorized_data.groupby(['app_display_name', 'app_name', 'category']).agg({
            'duration_minutes': 'sum'
        }).reset_index().sort_values('duration_minutes', ascending=False)
        
        for _, row in app_categories.iterrows():
            duration_h = row['duration_minutes'] / 60
            click.echo(f"  🏷️  {row['app_display_name']:<25} → {row['category']:<15} ({duration_h:.1f}h)")
        
        # Show category summary
        category_summary = mapper.get_category_summary(categorized_data)
        if not category_summary.empty:
            click.echo(f"\n📊 Category Usage Summary:")
            click.echo("-" * 40)
            for _, row in category_summary.iterrows():
                click.echo(f"  {row['category']:<15}: {row['duration_hours']:.1f}h ({row['percentage']:.1f}%) - {row['unique_apps']} apps")
        
        # Generate daily usage
        daily_usage = processor.aggregate_daily_usage(categorized_data)
        click.echo(f"\n📅 Generated {len(daily_usage)} daily usage records")
        
        # Show usage summary
        summary = processor.get_usage_summary(categorized_data)
        click.echo("\n📋 Overall Summary:")
        click.echo(f"  • Total apps: {summary['total_apps']}")
        click.echo(f"  • Total sessions: {summary['total_sessions']}")
        click.echo(f"  • Total usage: {summary['total_hours']} hours")
        click.echo(f"  • Average daily: {summary['avg_daily_usage']} hours")
        click.echo(f"  • Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        
        if not sync:
            click.echo(f"\n🔍 Test completed - add --sync to actually sync to Notion")
            click.echo(f"💡 Run 'screentime2notion categorize <app_name> <category>' to customize categories")
            return
        
        # Sync to Notion if requested
        click.echo(f"\n🔗 Connecting to Notion...")
        syncer = NotionSyncer(api_key, database_id)
        
        # Set up schema
        click.echo("⚙️ Setting up database schema...")
        syncer.setup_database_schema()
        
        # Sync data
        click.echo("🚀 Syncing test data to Notion...")
        results = syncer.sync_usage_data(daily_usage, batch_size=10)
        
        click.echo(f"\n✅ Test sync completed:")
        click.echo(f"  • Synced: {results['synced']} records")
        click.echo(f"  • Errors: {results['errors']} records")
        click.echo(f"  • Skipped: {results['skipped']} records")
        
        # Get database info
        db_info = syncer.get_database_info()
        if 'url' in db_info:
            click.echo(f"  • View in Notion: {db_info['url']}")
        
    except Exception as e:
        click.echo(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

@cli.command()
def devices():
    """Show all available devices with Screen Time data."""
    
    try:
        reader = ScreenTimeReader()
        devices = reader.get_available_devices()
        
        if not devices:
            click.echo("❌ No devices found")
            return
        
        click.echo("📱 Available Devices:")
        click.echo("=" * 50)
        
        for device in devices:
            click.echo(f"  {device['name']:<20} ({device['model']}) - {device['usage_count']} sessions")
        
        click.echo(f"\n💡 Found {len(devices)} device(s) with Screen Time data")
        click.echo("   Run 'screentime2notion sync' to include all devices")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
def clear_notion():
    """Clear all data from the Notion database."""
    
    api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not api_key or not database_id:
        click.echo("❌ Notion credentials not found")
        return
    
    if not click.confirm("⚠️  This will delete ALL data from your Notion database. Continue?"):
        click.echo("Cancelled")
        return
    
    try:
        syncer = NotionSyncer(api_key, database_id)
        click.echo("🗑️ Clearing Notion database...")
        
        if syncer.clear_database():
            click.echo("✅ Database cleared successfully")
        else:
            click.echo("❌ Failed to clear database")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

if __name__ == '__main__':
    cli()