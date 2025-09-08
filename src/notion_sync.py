import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import pandas as pd
from notion_client import Client
from notion_client.errors import APIResponseError, HTTPResponseError
import time

class NotionSyncer:
    def __init__(self, api_key: str, database_id: str):
        self.client = Client(auth=api_key)
        self.database_id = database_id
        self._verify_connection()

    def _verify_connection(self):
        try:
            # Test connection by retrieving database
            self.client.databases.retrieve(database_id=self.database_id)
            print("✓ Successfully connected to Notion")
        except (APIResponseError, HTTPResponseError) as e:
            raise Exception(f"Failed to connect to Notion: {e}")

    def setup_database_schema(self) -> bool:
        try:
            # Get current properties to avoid overwriting existing ones
            db = self.client.databases.retrieve(database_id=self.database_id)
            current_properties = db['properties']

            # Add missing columns
            new_properties = {}

            if "Category" not in current_properties:
                new_properties["Category"] = {
                    "select": {
                        "options": [
                            {"name": "Work", "color": "blue"},
                            {"name": "Learn", "color": "yellow"},
                            {"name": "Socialize", "color": "green"},
                            {"name": "Procrastinate", "color": "red"},
                            {"name": "Exercise", "color": "purple"},
                            {"name": "Family", "color": "pink"},
                            {"name": "Sleeping", "color": "gray"},
                            {"name": "Other", "color": "default"}
                        ]
                    }
                }

            if "Type" not in current_properties:
                new_properties["Type"] = {
                    "select": {
                        "options": [
                            {"name": "App", "color": "blue"},
                            {"name": "Website", "color": "green"}
                        ]
                    }
                }

            if "Domain" not in current_properties:
                new_properties["Domain"] = {"rich_text": {}}
            
            if "URL" not in current_properties:
                new_properties["URL"] = {"rich_text": {}}

            if "Last Updated" not in current_properties:
                new_properties["Last Updated"] = {"date": {}}

            if "Device" not in current_properties:
                new_properties["Device"] = {"rich_text": {}}

            # Update database properties only if we have new properties to add
            if new_properties:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties=new_properties
                )
                added_columns = list(new_properties.keys())
                print(f"✓ Added columns to database: {', '.join(added_columns)}")
            else:
                print("✓ Database schema is up to date")

            print("✓ Database schema updated successfully")
            return True

        except (APIResponseError, HTTPResponseError) as e:
            print(f"Error updating database schema: {e}")
            return False

    def sync_usage_data(self, daily_usage_df: pd.DataFrame, batch_size: int = 10) -> Dict[str, int]:
        if daily_usage_df.empty:
            return {"synced": 0, "errors": 0, "skipped": 0}

        results = {"synced": 0, "errors": 0, "skipped": 0}

        # Get existing entries to avoid duplicates
        existing_entries = self._get_existing_entries()

        # Process data in batches
        for i in range(0, len(daily_usage_df), batch_size):
            batch = daily_usage_df.iloc[i:i + batch_size]

            for _, row in batch.iterrows():
                try:
                    # Use app_name + date for unique key (works for both daily and weekly)
                    display_name = row.get('app_display_name', row['app_name'])
                    entry_key = f"{display_name}_{row['date']}"

                    # Skip if this would conflict with a manual entry
                    if hasattr(self, '_manual_entries') and entry_key in self._manual_entries:
                        print(f"⏭️ Skipping {display_name} ({row['date']}) - manual entry protected")
                        results["skipped"] += 1
                        continue

                    if entry_key in existing_entries:
                        # Update existing entry
                        success = self._update_notion_entry(existing_entries[entry_key], row)
                    else:
                        # Create new entry
                        success = self._create_notion_entry(row)

                    if success:
                        results["synced"] += 1
                    else:
                        results["errors"] += 1

                    # Rate limiting - Notion allows ~3 requests per second
                    time.sleep(0.35)

                except Exception as e:
                    print(f"Error processing row: {e}")
                    results["errors"] += 1

        return results

    def _get_existing_entries(self) -> Dict[str, str]:
        existing = {}
        manual_entries = set()

        try:
            # Query all existing entries
            response = self.client.databases.query(
                database_id=self.database_id,
                page_size=100
            )

            for page in response["results"]:
                properties = page["properties"]

                # Extract app name and date to create unique key
                app_name = self._extract_title(properties.get("App Name", {}))
                date_prop = properties.get("Date", {})

                # Check if this is a manual entry (has no App ID or has manual tag)
                app_id_prop = properties.get("App ID", {})
                app_id = self._extract_rich_text(app_id_prop)
                is_manual_entry = not app_id or app_id == "manual" or "manual" in app_name.lower()

                if app_name and date_prop.get("date", {}).get("start"):
                    date_str = date_prop["date"]["start"]
                    entry_key = f"{app_name}_{date_str}"
                    
                    if is_manual_entry:
                        manual_entries.add(entry_key)
                        print(f"🔒 Protecting manual entry: {app_name} ({date_str})")
                    else:
                        existing[entry_key] = page["id"]

            # Handle pagination
            while response.get("has_more"):
                response = self.client.databases.query(
                    database_id=self.database_id,
                    start_cursor=response["next_cursor"],
                    page_size=100
                )

                for page in response["results"]:
                    properties = page["properties"]
                    app_name = self._extract_title(properties.get("App Name", {}))
                    date_prop = properties.get("Date", {})
                    
                    app_id_prop = properties.get("App ID", {})
                    app_id = self._extract_rich_text(app_id_prop)
                    is_manual_entry = not app_id or app_id == "manual" or "manual" in app_name.lower()

                    if app_name and date_prop.get("date", {}).get("start"):
                        date_str = date_prop["date"]["start"]
                        entry_key = f"{app_name}_{date_str}"
                        
                        if is_manual_entry:
                            manual_entries.add(entry_key)
                            print(f"🔒 Protecting manual entry: {app_name} ({date_str})")
                        else:
                            existing[entry_key] = page["id"]

            print(f"Found {len(existing)} existing entries, {len(manual_entries)} manual entries protected")

        except (APIResponseError, HTTPResponseError) as e:
            print(f"Error fetching existing entries: {e}")

        # Store manual entries for later reference
        self._manual_entries = manual_entries
        return existing

    def _create_notion_entry(self, row: pd.Series) -> bool:
        try:
            properties = self._build_properties(row)

            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )

            return True

        except (APIResponseError, HTTPResponseError) as e:
            print(f"Error creating entry for {row['app_name']}: {e}")
            return False

    def _update_notion_entry(self, page_id: str, row: pd.Series) -> bool:
        try:
            properties = self._build_properties(row)

            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )

            return True

        except (APIResponseError, HTTPResponseError) as e:
            print(f"Error updating entry for {row['app_name']}: {e}")
            return False

    def _detect_app_type_and_domain(self, app_name: str, display_name: str) -> tuple[str, str]:
        """Detect if this is a website or app, and extract domain if website."""
        import os

        # Get browser apps and top domains from env
        browser_apps = os.getenv('BROWSER_APPS', '').split(',') if os.getenv('BROWSER_APPS') else []
        top_domains = os.getenv('TOP_DOMAINS', '').split(',') if os.getenv('TOP_DOMAINS') else []

        # Common website patterns in bundle IDs
        website_indicators = [
            '.webClipWrapper',  # Web clips
            'com.apple.WebKit.WebContent',  # WebKit content
            'com.google.Chrome.app.',  # Chrome web apps
            'com.microsoft.edgemac.app.',  # Edge web apps
            'org.mozilla.firefox.app.',  # Firefox web apps
        ]

        # Check if it's a website based on bundle ID
        for indicator in website_indicators:
            if indicator in app_name:
                domain = self._extract_domain(app_name, display_name)
                return "Website", domain

        # Check if this is a browser app from env config
        if app_name in browser_apps:
            # For browser apps, we can assign the most common domain or rotate through them
            # For now, let's use the first domain from the list as a default
            if top_domains:
                # You could implement logic here to distribute domains
                # For simplicity, let's use "web browsing" as domain
                return "Website", "web browsing"
            return "Website", ""

        # Default to App
        return "App", ""

    def _extract_domain(self, app_name: str, display_name: str) -> str:
        """Extract domain from app name or display name."""
        import re

        # Try to find domain patterns
        domain_patterns = [
            r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})',  # Basic domain pattern
            r'\.([a-zA-Z0-9-]+\.[a-zA-Z]{2,})\.',  # Domain in middle of bundle ID
        ]

        # First try app_name
        for pattern in domain_patterns:
            matches = re.findall(pattern, app_name)
            if matches:
                return matches[0]

        # Then try display_name
        for pattern in domain_patterns:
            matches = re.findall(pattern, display_name)
            if matches:
                return matches[0]

        return ""

    def _build_properties(self, row: pd.Series) -> Dict[str, Any]:
        # Convert date to ISO format string
        if isinstance(row['date'], date):
            date_str = row['date'].isoformat()
        else:
            date_str = str(row['date'])

        # Detect app type and domain
        app_type, domain = self._detect_app_type_and_domain(
            row['app_name'],
            row.get('app_display_name', row['app_name'])
        )

        # Get device name from the data or fallback to hostname
        if 'device_name' in row and row['device_name']:
            device_name = str(row['device_name'])
        else:
            import socket
            device_name = f"💻 {socket.gethostname().split('.')[0]}"

        properties = {
            "App Name": {
                "title": [{"text": {"content": str(row.get('app_display_name', row['app_name']))}}]
            },
            "App ID": {
                "rich_text": [{"text": {"content": str(row['app_name'])}}]
            },
            "Date": {
                "date": {"start": date_str}
            },
            "Minutes": {
                "number": float(row['duration_minutes'])
            },
            "Hours": {
                "number": float(row['duration_hours'])
            },
            "Sessions": {
                "number": int(row['session_count'])
            },
            "Type": {
                "select": {"name": app_type}
            },
            "Device": {
                "rich_text": [{"text": {"content": device_name}}]
            },
            "Last Updated": {
                "date": {"start": datetime.now().isoformat()}
            }
        }

        # Add domain if it exists
        if domain:
            properties["Domain"] = {
                "rich_text": [{"text": {"content": domain}}]
            }
        
        # Add URL if it exists (for web usage data)
        if 'url' in row and row['url'] and not pd.isna(row['url']):
            properties["URL"] = {
                "rich_text": [{"text": {"content": str(row['url'])}}]
            }

        # Add category if available
        if 'category' in row and row['category']:
            properties["Category"] = {
                "select": {"name": str(row['category'])}
            }

        # Add day of week if available
        if 'day_of_week' in row and row['day_of_week']:
            properties["Day of Week"] = {
                "select": {"name": str(row['day_of_week'])}
            }

        return properties

    def _extract_title(self, title_prop: Dict) -> Optional[str]:
        if not title_prop.get("title"):
            return None

        title_items = title_prop["title"]
        if not title_items:
            return None

        return title_items[0].get("plain_text", "")

    def _extract_rich_text(self, rich_text_prop: Dict) -> Optional[str]:
        if not rich_text_prop.get("rich_text"):
            return None

        rich_text_items = rich_text_prop["rich_text"]
        if not rich_text_items:
            return None

        return rich_text_items[0].get("plain_text", "")

    def get_database_info(self) -> Dict:
        try:
            db = self.client.databases.retrieve(database_id=self.database_id)
            return {
                "title": db.get("title", [{}])[0].get("plain_text", "Untitled"),
                "url": db.get("url", ""),
                "created_time": db.get("created_time", ""),
                "last_edited_time": db.get("last_edited_time", ""),
                "properties": list(db.get("properties", {}).keys())
            }
        except (APIResponseError, HTTPResponseError) as e:
            return {"error": str(e)}

    def create_summary_page(self, summary_data: Dict) -> Optional[str]:
        try:
            # Create a summary page with usage statistics
            content = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Screen Time Summary"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"Total Apps: {summary_data.get('total_apps', 0)}\n"}},
                            {"type": "text", "text": {"content": f"Total Sessions: {summary_data.get('total_sessions', 0)}\n"}},
                            {"type": "text", "text": {"content": f"Total Usage: {summary_data.get('total_hours', 0)} hours\n"}},
                            {"type": "text", "text": {"content": f"Average Daily Usage: {summary_data.get('avg_daily_usage', 0)} hours\n"}},
                            {"type": "text", "text": {"content": f"Date Range: {summary_data.get('date_range', {}).get('start', '')} to {summary_data.get('date_range', {}).get('end', '')}"}}
                        ]
                    }
                }
            ]

            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "App Name": {"title": [{"text": {"content": "📊 Usage Summary"}}]},
                    "Last Updated": {"date": {"start": datetime.now().isoformat()}}
                },
                children=content
            )

            return response["url"]

        except (APIResponseError, HTTPResponseError) as e:
            print(f"Error creating summary page: {e}")
            return None

    def clear_database(self) -> bool:
        try:
            # Get all pages in the database
            response = self.client.databases.query(database_id=self.database_id)

            deleted_count = 0
            for page in response["results"]:
                self.client.pages.update(
                    page_id=page["id"],
                    archived=True
                )
                deleted_count += 1
                time.sleep(0.1)  # Rate limiting

            # Handle pagination
            while response.get("has_more"):
                response = self.client.databases.query(
                    database_id=self.database_id,
                    start_cursor=response["next_cursor"]
                )

                for page in response["results"]:
                    self.client.pages.update(
                        page_id=page["id"],
                        archived=True
                    )
                    deleted_count += 1
                    time.sleep(0.1)

            print(f"Archived {deleted_count} pages")
            return True

        except (APIResponseError, HTTPResponseError) as e:
            print(f"Error clearing database: {e}")
            return False
