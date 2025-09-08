import sqlite3
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional
import pandas as pd

class ScreenTimeReader:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = self._find_knowledge_db()

    def _find_knowledge_db(self) -> str:
        home_dir = os.path.expanduser("~")
        knowledge_path = os.path.join(
            home_dir,
            "Library",
            "Application Support",
            "Knowledge",
            "knowledgeC.db"
        )

        if not os.path.exists(knowledge_path):
            raise FileNotFoundError(
                f"knowledgeC.db not found at {knowledge_path}. "
                "Make sure Screen Time is enabled and you have the necessary permissions."
            )

        return knowledge_path

    def _connect_to_db(self) -> sqlite3.Connection:
        try:
            # First try normal connection
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Test the connection by trying a simple query
            test_query = "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"
            cursor = conn.execute(test_query)
            cursor.fetchone()

            return conn
        except sqlite3.Error as e:
            # Try with read-only mode
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                conn.row_factory = sqlite3.Row
                return conn
            except sqlite3.Error as e2:
                raise Exception(f"Failed to connect to knowledgeC.db: {e} (also tried read-only: {e2})")

    def get_app_usage_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, include_all_devices: bool = True) -> pd.DataFrame:
        """Get app usage data from all devices or just local Mac."""
        
        if include_all_devices:
            query = """
            SELECT
                ZOBJECT.ZVALUESTRING as app_name,
                ZOBJECT.ZSTARTDATE as start_timestamp,
                ZOBJECT.ZENDDATE as end_timestamp,
                (ZOBJECT.ZENDDATE - ZOBJECT.ZSTARTDATE) as duration_seconds,
                ZOBJECT.ZCREATIONDATE as creation_date,
                ZOBJECT.ZSTREAMNAME as stream_name,
                ZOBJECT.ZSECONDSFROMGMT as timezone_offset,
                COALESCE(ZSYNCPEER.ZMODEL, 'Mac') as device_model,
                COALESCE(ZSYNCPEER.ZDEVICEID, 'local') as device_id
            FROM ZOBJECT
            LEFT JOIN ZSTRUCTUREDMETADATA ON ZSTRUCTUREDMETADATA.Z_PK = ZOBJECT.ZSTRUCTUREDMETADATA
            LEFT JOIN ZSOURCE ON ZOBJECT.ZSOURCE = ZSOURCE.Z_PK
            LEFT JOIN ZSYNCPEER ON ZSOURCE.ZDEVICEID = ZSYNCPEER.ZDEVICEID
            WHERE ZOBJECT.ZSTREAMNAME LIKE '/app/usage'
            AND ZOBJECT.ZVALUESTRING IS NOT NULL
            AND ZOBJECT.ZVALUESTRING != ''
            AND (ZOBJECT.ZENDDATE - ZOBJECT.ZSTARTDATE) > 15
            """
        else:
            query = """
            SELECT
                ZOBJECT.ZVALUESTRING as app_name,
                ZOBJECT.ZSTARTDATE as start_timestamp,
                ZOBJECT.ZENDDATE as end_timestamp,
                (ZOBJECT.ZENDDATE - ZOBJECT.ZSTARTDATE) as duration_seconds,
                ZOBJECT.ZCREATIONDATE as creation_date,
                ZOBJECT.ZSTREAMNAME as stream_name,
                ZOBJECT.ZSECONDSFROMGMT as timezone_offset,
                'Mac' as device_model,
                'local' as device_id
            FROM ZOBJECT
            WHERE ZOBJECT.ZSTREAMNAME LIKE '/app/usage'
            AND ZOBJECT.ZVALUESTRING IS NOT NULL
            AND ZOBJECT.ZVALUESTRING != ''
            """

        params = []
        if start_date:
            # Convert to Mac timestamp (seconds since 2001-01-01)
            mac_start = (start_date.timestamp() - 978307200)
            query += " AND ZOBJECT.ZSTARTDATE >= ?"
            params.append(mac_start)

        if end_date:
            mac_end = (end_date.timestamp() - 978307200)
            query += " AND ZOBJECT.ZENDDATE <= ?"
            params.append(mac_end)

        query += " ORDER BY ZOBJECT.ZSTARTDATE DESC"

        with self._connect_to_db() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        if df.empty:
            return pd.DataFrame()

        # Convert Mac timestamps to datetime objects
        df['start_time'] = df['start_timestamp'].apply(self._mac_timestamp_to_datetime)
        df['end_time'] = df['end_timestamp'].apply(self._mac_timestamp_to_datetime)
        df['creation_time'] = df['creation_date'].apply(self._mac_timestamp_to_datetime)

        # Calculate duration in minutes
        df['duration_minutes'] = df['duration_seconds'] / 60

        # Clean up app names and add device info
        df['app_display_name'] = df['app_name'].apply(self._clean_app_name)
        df['device_name'] = df['device_model'].apply(self._format_device_name)

        return df[['app_name', 'app_display_name', 'start_time', 'end_time', 'duration_minutes', 'creation_time', 'device_model', 'device_name', 'device_id']]

    def _mac_timestamp_to_datetime(self, mac_timestamp: float) -> datetime:
        if pd.isna(mac_timestamp):
            return None

        # Mac timestamps are seconds since 2001-01-01 00:00:00 UTC
        unix_timestamp = mac_timestamp + 978307200
        return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)

    def _clean_app_name(self, app_name: str) -> str:
        if not app_name:
            return app_name

        # Manual mappings for known apps
        app_mappings = {
            'company.thebrowser.Browser': 'Arc',
            'com.figma.Desktop': 'Figma',
            'com.todesktop.230313mzl4w4u92': 'Cursor',  # Common ToDesktop app
            'notion.id': 'Notion',
            'com.adobe.Photoshop': 'Photoshop',
            'com.adobe.illustrator': 'Illustrator',
            'com.spotify.client': 'Spotify',
            'com.readdle.smartemail-Mac': 'Spark Email',
            'us.zoom.xos': 'Zoom',
            'com.apple.FaceTime': 'FaceTime',
            'com.apple.Safari': 'Safari',
            'com.apple.finder': 'Finder',
            'com.d1v1b.ToWebP2': 'ToWebP',
            'com.garagecube.MadMapperDemo': 'MadMapper',
            'com.apple.systempreferences': 'System Preferences'
        }

        # Check for exact match first
        if app_name in app_mappings:
            return app_mappings[app_name]

        # If it looks like a bundle identifier, try to extract app name
        if '.' in app_name and app_name.count('.') >= 2:
            # Extract last component after the last dot
            parts = app_name.split('.')
            if len(parts) > 1:
                cleaned = parts[-1]
                # Handle special cases
                if cleaned.lower() == 'desktop':
                    # Look at the second to last part
                    if len(parts) > 2:
                        return parts[-2].capitalize()
                # Capitalize first letter
                return cleaned.capitalize()

        return app_name

    def _format_device_name(self, device_model: str) -> str:
        """Format device model into a readable name with emoji."""
        if pd.isna(device_model) or not device_model or device_model == 'Mac':
            return '💻 Mac'
        
        device_map = {
            'iMac14,1': '🖥️ iMac',
            'iPad8,11': '📱 iPad Pro',
            'iPhone12,8': '📱 iPhone 12 mini',
            'iPhone13,3': '📱 iPhone 14 Pro',
            'iPhone16,2': '📱 iPhone 16 Pro',
        }
        
        return device_map.get(device_model, f'📱 {device_model}')

    def get_available_devices(self) -> List[Dict]:
        """Get all available devices in the Screen Time database."""
        query = """
        SELECT DISTINCT
            ZSYNCPEER.ZMODEL as device_model,
            ZSYNCPEER.ZDEVICEID as device_id,
            COUNT(*) as usage_count
        FROM ZOBJECT
        LEFT JOIN ZSTRUCTUREDMETADATA ON ZSTRUCTUREDMETADATA.Z_PK = ZOBJECT.ZSTRUCTUREDMETADATA
        LEFT JOIN ZSOURCE ON ZOBJECT.ZSOURCE = ZSOURCE.Z_PK
        LEFT JOIN ZSYNCPEER ON ZSOURCE.ZDEVICEID = ZSYNCPEER.ZDEVICEID
        WHERE ZOBJECT.ZSTREAMNAME LIKE '/app/usage'
        AND ZOBJECT.ZVALUESTRING IS NOT NULL
        AND ZSYNCPEER.ZMODEL IS NOT NULL
        GROUP BY ZSYNCPEER.ZMODEL, ZSYNCPEER.ZDEVICEID
        ORDER BY usage_count DESC
        """
        
        with self._connect_to_db() as conn:
            cursor = conn.execute(query)
            devices = []
            for row in cursor.fetchall():
                device_model = row['device_model']
                devices.append({
                    'model': device_model,
                    'id': row['device_id'],
                    'name': self._format_device_name(device_model),
                    'usage_count': row['usage_count']
                })
        
        # Add Mac (local device) if not already present
        mac_found = any(d['model'] in ['Mac', 'iMac14,1'] for d in devices)
        if not mac_found:
            devices.insert(0, {
                'model': 'Mac',
                'id': 'local',
                'name': '💻 Mac',
                'usage_count': 0
            })
        
        return devices

    def get_available_apps(self) -> List[str]:
        query = """
        SELECT DISTINCT ZOBJECT.ZVALUESTRING as app_name
        FROM ZOBJECT
        WHERE ZOBJECT.ZSTREAMNAME LIKE '/app/usage'
        AND ZOBJECT.ZVALUESTRING IS NOT NULL
        AND ZOBJECT.ZVALUESTRING != ''
        ORDER BY app_name
        """

        with self._connect_to_db() as conn:
            cursor = conn.execute(query)
            apps = [row['app_name'] for row in cursor.fetchall()]

        return apps

    def get_device_info(self) -> Dict:
        query = """
        SELECT DISTINCT
            ZOBJECT.ZSOURCE as device_source,
            ZOBJECT.ZSTREAMNAME as stream_name
        FROM ZOBJECT
        WHERE ZOBJECT.ZSTREAMNAME LIKE '/app/usage'
        LIMIT 10
        """

        with self._connect_to_db() as conn:
            cursor = conn.execute(query)
            devices = cursor.fetchall()

        return [dict(row) for row in devices]
