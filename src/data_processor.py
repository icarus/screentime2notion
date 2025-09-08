import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

class DataProcessor:
    def __init__(self, timezone_str: str = "UTC"):
        self.timezone = pytz.timezone(timezone_str)
    
    def process_usage_sessions(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        if raw_data.empty:
            return pd.DataFrame()
        
        # Convert timezone-naive datetimes to timezone-aware
        df = raw_data.copy()
        
        # Handle timezone conversion properly - check if already timezone-aware
        if df['start_time'].dt.tz is None:
            df['start_time'] = pd.to_datetime(df['start_time']).dt.tz_localize('UTC').dt.tz_convert(self.timezone)
        else:
            df['start_time'] = pd.to_datetime(df['start_time']).dt.tz_convert(self.timezone)
            
        if df['end_time'].dt.tz is None:
            df['end_time'] = pd.to_datetime(df['end_time']).dt.tz_localize('UTC').dt.tz_convert(self.timezone)
        else:
            df['end_time'] = pd.to_datetime(df['end_time']).dt.tz_convert(self.timezone)
        
        # Filter out sessions that are too short (less than 5 seconds) or too long (more than 12 hours)
        df = df[
            (df['duration_minutes'] >= 0.083) &  # 5 seconds in minutes
            (df['duration_minutes'] <= 720)      # 12 hours in minutes
        ]
        
        # Sort by app and start time for processing
        df = df.sort_values(['app_name', 'start_time'])
        
        # Merge overlapping sessions for the same app
        processed_sessions = self._merge_overlapping_sessions(df)
        
        # Add date column for grouping
        processed_sessions['date'] = processed_sessions['start_time'].dt.date
        
        # Add day of week
        processed_sessions['day_of_week'] = processed_sessions['start_time'].dt.day_name()
        
        # Add hour of day for time-based analysis
        processed_sessions['start_hour'] = processed_sessions['start_time'].dt.hour
        
        return processed_sessions.sort_values('start_time', ascending=False)
    
    def _merge_overlapping_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        merged_sessions = []
        
        # Group by app name to process sessions for each app separately
        for app_name in df['app_name'].unique():
            app_sessions = df[df['app_name'] == app_name].sort_values('start_time')
            
            if len(app_sessions) == 0:
                continue
            
            # Start with the first session
            current_session = app_sessions.iloc[0].copy()
            
            for idx in range(1, len(app_sessions)):
                next_session = app_sessions.iloc[idx]
                
                # Check if sessions overlap or are within 5 minutes of each other
                gap_minutes = (next_session['start_time'] - current_session['end_time']).total_seconds() / 60
                
                if gap_minutes <= 5:  # Merge sessions within 5 minutes
                    # Extend current session to include next session
                    current_session['end_time'] = max(current_session['end_time'], next_session['end_time'])
                    current_session['duration_minutes'] = (
                        current_session['end_time'] - current_session['start_time']
                    ).total_seconds() / 60
                else:
                    # Sessions don't overlap, save current and start new one
                    merged_sessions.append(current_session)
                    current_session = next_session.copy()
            
            # Don't forget the last session
            merged_sessions.append(current_session)
        
        if not merged_sessions:
            return pd.DataFrame()
        
        return pd.DataFrame(merged_sessions)
    
    def aggregate_daily_usage(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        if processed_data.empty:
            return pd.DataFrame()
        
        # Group by date, app, and category (if present)
        group_columns = ['date', 'app_name', 'app_display_name']
        if 'category' in processed_data.columns:
            group_columns.append('category')
        if 'device_name' in processed_data.columns:
            group_columns.append('device_name')
        
        daily_usage = processed_data.groupby(group_columns).agg({
            'duration_minutes': 'sum',
            'start_time': 'count'  # Number of sessions
        }).reset_index()
        
        daily_usage.rename(columns={'start_time': 'session_count'}, inplace=True)
        
        # Convert duration to hours for easier reading
        daily_usage['duration_hours'] = daily_usage['duration_minutes'] / 60
        
        # Round to 2 decimal places
        daily_usage['duration_hours'] = daily_usage['duration_hours'].round(2)
        daily_usage['duration_minutes'] = daily_usage['duration_minutes'].round(1)
        
        return daily_usage.sort_values(['date', 'duration_minutes'], ascending=[False, False])
    
    def aggregate_weekly_usage(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate usage by week - one row per app per week."""
        if processed_data.empty:
            return pd.DataFrame()
        
        # Add week column (start of week - Monday)
        # Convert to timezone-naive first to avoid warning
        processed_data_copy = processed_data.copy()
        processed_data_copy['start_time_local'] = processed_data_copy['start_time'].dt.tz_localize(None)
        processed_data_copy['week_start'] = processed_data_copy['start_time_local'].dt.to_period('W-MON').dt.start_time.dt.date
        
        # Group by week, app, and category (if present)
        group_columns = ['week_start', 'app_name', 'app_display_name']
        if 'category' in processed_data_copy.columns:
            group_columns.append('category')
        if 'device_name' in processed_data_copy.columns:
            group_columns.append('device_name')
        
        weekly_usage = processed_data_copy.groupby(group_columns).agg({
            'duration_minutes': 'sum',
            'start_time': 'count'  # Number of sessions
        }).reset_index()
        
        weekly_usage.rename(columns={
            'start_time': 'session_count',
            'week_start': 'date'  # Keep 'date' column name for compatibility
        }, inplace=True)
        
        # Convert duration to hours
        weekly_usage['duration_hours'] = weekly_usage['duration_minutes'] / 60
        
        # Round to reasonable precision
        weekly_usage['duration_hours'] = weekly_usage['duration_hours'].round(2)
        weekly_usage['duration_minutes'] = weekly_usage['duration_minutes'].round(1)
        
        return weekly_usage.sort_values(['date', 'duration_minutes'], ascending=[False, False])
    
    def get_usage_summary(self, processed_data: pd.DataFrame) -> Dict:
        if processed_data.empty:
            return {
                'total_apps': 0,
                'total_sessions': 0,
                'total_hours': 0,
                'date_range': None,
                'avg_daily_usage': 0
            }
        
        total_sessions = len(processed_data)
        total_minutes = processed_data['duration_minutes'].sum()
        total_hours = total_minutes / 60
        unique_apps = processed_data['app_name'].nunique()
        
        date_range = {
            'start': processed_data['start_time'].min().strftime('%Y-%m-%d'),
            'end': processed_data['start_time'].max().strftime('%Y-%m-%d')
        }
        
        # Calculate average daily usage
        unique_dates = processed_data['date'].nunique()
        avg_daily_usage = total_hours / unique_dates if unique_dates > 0 else 0
        
        return {
            'total_apps': unique_apps,
            'total_sessions': total_sessions,
            'total_hours': round(total_hours, 2),
            'total_minutes': round(total_minutes, 1),
            'date_range': date_range,
            'avg_daily_usage': round(avg_daily_usage, 2),
            'unique_dates': unique_dates
        }