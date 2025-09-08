import pandas as pd
import random
from datetime import datetime, timedelta
from typing import List, Dict

class TestDataGenerator:
    def __init__(self):
        self.sample_apps = [
            ('com.apple.Safari', 'Safari'),
            ('com.microsoft.VSCode', 'Visual Studio Code'),
            ('com.notion.desktop', 'Notion'),
            ('com.figma.Desktop', 'Figma'),
            ('com.apple.Terminal', 'Terminal'),
            ('com.spotify.client', 'Spotify'),
            ('com.google.Chrome', 'Chrome'),
            ('com.slack.Slack', 'Slack'),
            ('com.apple.Xcode', 'Xcode'),
            ('com.adobe.Photoshop', 'Photoshop'),
        ]
    
    def generate_realistic_usage_data(self, days: int) -> pd.DataFrame:
        """Generate realistic Screen Time usage data for testing."""
        
        sessions = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate sessions for each day
        current_date = start_date
        while current_date <= end_date:
            # Generate 10-50 sessions per day
            daily_sessions = random.randint(10, 50)
            
            for _ in range(daily_sessions):
                app_bundle, app_display = random.choice(self.sample_apps)
                
                # Generate random start time during the day
                hour = random.randint(8, 22)  # 8 AM to 10 PM
                minute = random.randint(0, 59)
                start_time = current_date.replace(hour=hour, minute=minute, second=0)
                
                # Generate session duration (1 minute to 2 hours)
                duration_minutes = random.uniform(1, 120)
                end_time = start_time + timedelta(minutes=duration_minutes)
                
                sessions.append({
                    'app_name': app_bundle,
                    'app_display_name': app_display,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_minutes': duration_minutes,
                    'creation_time': start_time,
                    'device_name': '💻 Mac'
                })
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(sessions)