import json
import os
import pandas as pd
from typing import Dict, List, Set, Optional
import re
from pathlib import Path

class CategoryMapper:
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = config_path
        else:
            # Default to config/categories.json in the project root
            project_root = Path(__file__).parent.parent
            self.config_path = project_root / "config" / "categories.json"
        
        self.categories = self._load_categories()
        
    def _load_categories(self) -> Dict:
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config.get('categories', {})
        except FileNotFoundError:
            print(f"Warning: Category config file not found at {self.config_path}")
            return self._get_default_categories()
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in config file: {e}")
            return self._get_default_categories()
    
    def _get_default_categories(self) -> Dict:
        return {
            "Work": {
                "color": "blue",
                "apps": ["Safari", "Terminal", "Xcode", "Visual Studio Code"],
                "bundle_patterns": ["com.microsoft.*", "com.apple.dt.Xcode"]
            },
            "Other": {
                "color": "default", 
                "apps": [],
                "bundle_patterns": []
            }
        }
    
    def categorize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        df_copy = df.copy()
        df_copy['category'] = df_copy.apply(
            lambda row: self.categorize_app(row['app_name'], row.get('app_display_name', '')),
            axis=1
        )
        
        return df_copy
    
    def categorize_app(self, app_name: str, display_name: str = "") -> str:
        app_name = str(app_name) if app_name else ""
        display_name = str(display_name) if display_name else ""
        
        # Check each category
        for category_name, category_config in self.categories.items():
            # Check direct app name matches
            apps = category_config.get('apps', [])
            if display_name in apps or app_name in apps:
                return category_name
            
            # Check bundle pattern matches
            patterns = category_config.get('bundle_patterns', [])
            for pattern in patterns:
                if re.search(pattern.replace('*', '.*'), app_name, re.IGNORECASE):
                    return category_name
        
        return "Other"
    
    def get_available_categories(self) -> List[str]:
        return list(self.categories.keys())
    
    def add_custom_mapping(self, app_name: str, category: str) -> bool:
        if category not in self.categories:
            print(f"Category '{category}' not found. Available: {self.get_available_categories()}")
            return False
        
        # Add to the category's apps list
        if app_name not in self.categories[category]['apps']:
            self.categories[category]['apps'].append(app_name)
            return self._save_categories()
        
        return True
    
    def _save_categories(self) -> bool:
        try:
            config = {'categories': self.categories}
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving categories: {e}")
            return False
    
    def get_uncategorized_apps(self, df: pd.DataFrame) -> Set[str]:
        if df.empty:
            return set()
        
        categorized = self.categorize_dataframe(df)
        uncategorized = categorized[categorized['category'] == 'Other']
        
        return set(uncategorized['app_display_name'].unique())
    
    def get_category_summary(self, categorized_df: pd.DataFrame) -> pd.DataFrame:
        if categorized_df.empty:
            return pd.DataFrame()
        
        summary = categorized_df.groupby('category').agg({
            'duration_minutes': 'sum',
            'app_name': 'nunique'
        }).reset_index()
        
        summary.rename(columns={
            'duration_minutes': 'total_minutes',
            'app_name': 'unique_apps'
        }, inplace=True)
        
        summary['duration_hours'] = (summary['total_minutes'] / 60).round(2)
        total_minutes = summary['total_minutes'].sum()
        
        if total_minutes > 0:
            summary['percentage'] = ((summary['total_minutes'] / total_minutes) * 100).round(1)
        else:
            summary['percentage'] = 0
        
        return summary.sort_values('total_minutes', ascending=False)