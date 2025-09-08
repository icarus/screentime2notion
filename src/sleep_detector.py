import sqlite3
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional, List

class SleepDetector:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _connect_to_db(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            raise Exception(f"Failed to connect to knowledgeC.db: {e}")
    
    def _mac_timestamp_to_datetime(self, mac_timestamp: float) -> datetime:
        if pd.isna(mac_timestamp):
            return None
        # Mac timestamps are seconds since 2001-01-01 00:00:00 UTC
        unix_timestamp = mac_timestamp + 978307200
        return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    
    def get_sleep_sessions(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Detect sleep sessions by analyzing display backlight data.
        Long periods of display OFF (4+ hours between 8PM and 10AM) are considered sleep.
        """
        query = """
        SELECT 
            ZSTARTDATE as start_timestamp,
            ZENDDATE as end_timestamp,
            ZVALUEINTEGER as is_backlit,
            (ZENDDATE - ZSTARTDATE) as duration_seconds
        FROM ZOBJECT 
        WHERE ZSTREAMNAME = '/display/isBacklit'
        AND ZVALUEINTEGER = 0  -- Display OFF
        """
        
        params = []
        if start_date:
            mac_start = (start_date.timestamp() - 978307200)
            query += " AND ZSTARTDATE >= ?"
            params.append(mac_start)
        
        if end_date:
            mac_end = (end_date.timestamp() - 978307200)
            query += " AND ZENDDATE <= ?"
            params.append(mac_end)
        
        query += " ORDER BY ZSTARTDATE DESC"
        
        with self._connect_to_db() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        if df.empty:
            return pd.DataFrame()
        
        # Convert timestamps
        df['start_time'] = df['start_timestamp'].apply(self._mac_timestamp_to_datetime)
        df['end_time'] = df['end_timestamp'].apply(self._mac_timestamp_to_datetime)
        df['duration_hours'] = df['duration_seconds'] / 3600
        df['duration_minutes'] = df['duration_seconds'] / 60
        
        # Filter for potential sleep sessions
        sleep_sessions = []
        
        for _, row in df.iterrows():
            duration_hours = row['duration_hours']
            start_time = row['start_time']
            
            # Sleep detection criteria:
            # 1. Display OFF for 3+ hours
            # 2. Started between 8PM and 2AM OR ended between 5AM and 11AM
            if duration_hours >= 3:
                start_hour = start_time.hour
                end_hour = row['end_time'].hour
                
                # Likely sleep if starts in evening (20-02) or ends in morning (05-11)
                is_evening_start = start_hour >= 20 or start_hour <= 2
                is_morning_end = 5 <= end_hour <= 11
                
                if is_evening_start or is_morning_end:
                    sleep_sessions.append({
                        'app_name': 'sleep.session',
                        'app_display_name': 'Sleep',
                        'start_time': row['start_time'],
                        'end_time': row['end_time'],
                        'duration_minutes': row['duration_minutes'],
                        'duration_hours': duration_hours,
                        'category': 'Sleeping',
                        'session_type': 'sleep',
                        'device_name': '💻 Mac'
                    })
        
        if not sleep_sessions:
            return pd.DataFrame()
        
        sleep_df = pd.DataFrame(sleep_sessions)
        
        # Add date and day info
        sleep_df['date'] = sleep_df['start_time'].dt.date
        sleep_df['day_of_week'] = sleep_df['start_time'].dt.day_name()
        sleep_df['start_hour'] = sleep_df['start_time'].dt.hour
        
        return sleep_df.sort_values('start_time', ascending=False)
    
    def get_sleep_summary(self, processed_sleep_data: pd.DataFrame) -> dict:
        """Get sleep statistics summary"""
        if processed_sleep_data.empty:
            return {
                'total_sleep_hours': 0,
                'avg_sleep_hours': 0,
                'sleep_sessions': 0,
                'date_range': None
            }
        
        total_hours = processed_sleep_data['duration_hours'].sum()
        avg_hours = processed_sleep_data['duration_hours'].mean()
        sessions = len(processed_sleep_data)
        
        date_range = {
            'start': processed_sleep_data['start_time'].min().strftime('%Y-%m-%d'),
            'end': processed_sleep_data['start_time'].max().strftime('%Y-%m-%d')
        }
        
        return {
            'total_sleep_hours': round(total_hours, 2),
            'avg_sleep_hours': round(avg_hours, 2),
            'sleep_sessions': sessions,
            'date_range': date_range
        }