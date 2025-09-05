# config/web_config.py
"""
Configuration for web integration
"""

import os
import json

class WebConfig:
    """Configuration for web API integration"""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "web_api_url": "http://localhost:8000/api",
        "website_url": "https://scrapeon.com",
        "dashboard_url": "https://scrapeon.com/dashboard",
        "billing_url": "https://scrapeon.com/billing",
        "register_url": "https://scrapeon.com/register",
        "enable_web_sync": True,
        "sync_timeout": 5,
        "offline_mode": False
    }
    
    def __init__(self):
        self.config_file = "config/web_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                merged_config = self.DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
            except:
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
    
    def update(self, updates):
        """Update multiple configuration values"""
        self.config.update(updates)
        self.save_config()

# Create global config instance
web_config = WebConfig()

