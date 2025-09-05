# config/app_config.py
"""
Main application configuration
"""

import os

class AppConfig:
    """Main application configuration"""
    
    # Application info
    APP_NAME = "ScrapeOn"
    VERSION = "2.0.0"
    DESCRIPTION = "Advanced Web Scraping Platform"
    
    # Database
    DATABASE_PATH = "data/scrapeon.db"
    
    # UI Configuration
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 750
    MIN_WIDTH = 900
    MIN_HEIGHT = 650
    
    # Theme settings
    APPEARANCE_MODE = "dark"  # "light", "dark", "system"
    COLOR_THEME = "blue"      # "blue", "green", "dark-blue"
    
    # Scraping limits (fallback if not in database)
    DEFAULT_LIMITS = {
        "max_pages": 5,
        "max_results_per_scrape": 50,
        "timeout": 30,
        "delay_between_requests": 1,
        "max_retries": 3
    }
    
    # File paths
    DATA_DIR = "data"
    RESULTS_DIR = "results"
    EXPORTS_DIR = "exports"
    BACKUPS_DIR = "backups"
    CONFIG_DIR = "config"
    LOGS_DIR = "logs"
    
    # Export settings
    EXPORT_FORMATS = ["xlsx", "csv", "json"]
    DEFAULT_EXPORT_FORMAT = "xlsx"
    
    # Logging configuration
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE = "logs/scrapeon.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Security settings
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes in seconds
    
    # Performance settings
    MAX_CONCURRENT_SCRAPERS = 3
    DEFAULT_TIMEOUT = 30
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Feature flags
    ENABLE_AUTO_UPDATES = True
    ENABLE_ANALYTICS = True
    ENABLE_ERROR_REPORTING = True
    ENABLE_OFFLINE_MODE = True
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.DATA_DIR,
            cls.RESULTS_DIR,
            cls.EXPORTS_DIR,
            cls.BACKUPS_DIR,
            cls.CONFIG_DIR,
            cls.LOGS_DIR
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"✓ Directory ensured: {directory}")
            except Exception as e:
                print(f"✗ Failed to create directory {directory}: {e}")
    
    @classmethod
    def get_full_path(cls, relative_path):
        """Get full path from relative path"""
        return os.path.abspath(relative_path)
    
    @classmethod
    def get_database_url(cls):
        """Get database connection URL"""
        return f"sqlite:///{cls.get_full_path(cls.DATABASE_PATH)}"
    
    @classmethod
    def get_log_file_path(cls):
        """Get full log file path"""
        return cls.get_full_path(cls.LOG_FILE)
    
    @classmethod
    def validate_config(cls):
        """Validate configuration values"""
        errors = []
        
        # Check if required directories can be created
        try:
            cls.ensure_directories()
        except Exception as e:
            errors.append(f"Cannot create required directories: {e}")
        
        # Validate numeric values
        if cls.WINDOW_WIDTH < cls.MIN_WIDTH:
            errors.append(f"WINDOW_WIDTH ({cls.WINDOW_WIDTH}) must be >= MIN_WIDTH ({cls.MIN_WIDTH})")
        
        if cls.WINDOW_HEIGHT < cls.MIN_HEIGHT:
            errors.append(f"WINDOW_HEIGHT ({cls.WINDOW_HEIGHT}) must be >= MIN_HEIGHT ({cls.MIN_HEIGHT})")
        
        if cls.SESSION_TIMEOUT <= 0:
            errors.append("SESSION_TIMEOUT must be positive")
        
        if cls.MAX_LOGIN_ATTEMPTS <= 0:
            errors.append("MAX_LOGIN_ATTEMPTS must be positive")
        
        # Validate string values
        valid_themes = ["blue", "green", "dark-blue"]
        if cls.COLOR_THEME not in valid_themes:
            errors.append(f"COLOR_THEME must be one of: {valid_themes}")
        
        valid_appearance = ["light", "dark", "system"]
        if cls.APPEARANCE_MODE not in valid_appearance:
            errors.append(f"APPEARANCE_MODE must be one of: {valid_appearance}")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {valid_log_levels}")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("=" * 50)
        print(f"{cls.APP_NAME} v{cls.VERSION} Configuration")
        print("=" * 50)
        print(f"Database: {cls.DATABASE_PATH}")
        print(f"Results: {cls.RESULTS_DIR}")
        print(f"Window Size: {cls.WINDOW_WIDTH}x{cls.WINDOW_HEIGHT}")
        print(f"Theme: {cls.COLOR_THEME} ({cls.APPEARANCE_MODE})")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"Session Timeout: {cls.SESSION_TIMEOUT}s")
        print("=" * 50)

# Development vs Production configurations
class DevelopmentConfig(AppConfig):
    """Development environment configuration"""
    LOG_LEVEL = "DEBUG"
    ENABLE_ERROR_REPORTING = False
    SESSION_TIMEOUT = 7200  # 2 hours
    
class ProductionConfig(AppConfig):
    """Production environment configuration"""
    LOG_LEVEL = "WARNING"
    ENABLE_ERROR_REPORTING = True
    SESSION_TIMEOUT = 1800  # 30 minutes
    ENABLE_AUTO_UPDATES = True

# Function to get appropriate config based on environment
def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('SCRAPEON_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig
    else:
        return DevelopmentConfig

# Default config instance
app_config = get_config()