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
        
        self.ios_apps = [
            ('com.apple.mobilesafari', 'Safari'),
            ('com.twitter.twitter', 'Twitter'),
            ('com.instagram.instagram', 'Instagram'),
            ('com.tinyspeck.chatlyio', 'Slack'),
            ('com.spotify.client', 'Spotify'),
            ('com.apple.mobilenotes', 'Notes'),
            ('com.apple.mobilemail', 'Mail'),
            ('com.apple.MobileSMS', 'Messages'),
            ('com.notion.Notion', 'Notion'),
            ('com.microsoft.Office.Outlook', 'Outlook'),
        ]
        
        self.devices = [
            ('💻 Mac', 'Mac', 'local'),
            ('📱 iPhone 15 Pro', 'iPhone16,1', 'iphone-12345'),
            ('📱 iPad Pro 12.9"', 'iPad8,11', 'ipad-67890'),
        ]
    
    def generate_realistic_usage_data(self, days: int) -> pd.DataFrame:
        """Generate realistic Screen Time usage data for testing."""
        
        sessions = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate sessions for each day
        current_date = start_date
        while current_date <= end_date:
            # Generate sessions for each device
            for device_name, device_model, device_id in self.devices:
                # Different session counts per device type
                if 'Mac' in device_name:
                    daily_sessions = random.randint(15, 40)
                    apps_to_use = self.sample_apps
                elif 'iPhone' in device_name:
                    daily_sessions = random.randint(20, 60)  # iPhones typically have more sessions
                    apps_to_use = self.ios_apps
                else:  # iPad
                    daily_sessions = random.randint(5, 25)
                    apps_to_use = self.ios_apps
                
                for _ in range(daily_sessions):
                    app_bundle, app_display = random.choice(apps_to_use)
                    
                    # Generate random start time during the day
                    hour = random.randint(8, 22)  # 8 AM to 10 PM
                    minute = random.randint(0, 59)
                    start_time = current_date.replace(hour=hour, minute=minute, second=0)
                    
                    # Generate session duration based on device
                    if 'iPhone' in device_name:
                        duration_minutes = random.uniform(0.5, 45)  # Shorter iOS sessions
                    elif 'iPad' in device_name:
                        duration_minutes = random.uniform(2, 90)    # Medium iPad sessions
                    else:  # Mac
                        duration_minutes = random.uniform(1, 120)   # Longer Mac sessions
                    
                    end_time = start_time + timedelta(minutes=duration_minutes)
                    
                    session_data = {
                        'app_name': app_bundle,
                        'app_display_name': app_display,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration_minutes': duration_minutes,
                        'creation_time': start_time,
                        'device_name': device_name,
                        'device_model': device_model,
                        'device_id': device_id,
                        'gmt_offset': -8.0  # Pacific timezone
                    }
                    
                    # Add URL for some iOS Safari sessions (simulating web usage)
                    if app_bundle == 'com.apple.mobilesafari' and random.random() < 0.7:
                        urls = ['https://www.google.com', 'https://www.apple.com', 'https://www.github.com', 
                               'https://www.twitter.com', 'https://www.youtube.com']
                        session_data['url'] = random.choice(urls)
                    
                    sessions.append(session_data)
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(sessions)