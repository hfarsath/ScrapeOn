#!/usr/bin/env python3
"""
ScrapeOn - Advanced Web Scraping Application with Web Integration
Main entry point for the application
"""

import tkinter as tk
import customtkinter as ctk
from auth.login import LoginWindow
from gui.main_window import MainWindow
from config.theme import ScrapeOnTheme
from config.web_config import web_config
from config.app_config import app_config
from database.models import DatabaseManager
import os
import sys
import logging

class ScrapeOnApp:
    def __init__(self):
        self.current_user = None
        self.db_manager = None
        
        self.setup_logging()
        self.setup_app_appearance()
        self.create_directories()
        self.initialize_database()
        
    def setup_logging(self):
        """Setup application logging"""
        try:
            # Ensure logs directory exists
            os.makedirs(os.path.dirname(app_config.LOG_FILE), exist_ok=True)
            
            # Configure logging
            logging.basicConfig(
                level=getattr(logging, app_config.LOG_LEVEL),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(app_config.LOG_FILE),
                    logging.StreamHandler()
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Starting {app_config.APP_NAME} v{app_config.VERSION}")
            
        except Exception as e:
            print(f"Warning: Could not setup logging: {e}")
            self.logger = None
        
    def setup_app_appearance(self):
        """Configure the appearance of the application"""
        try:
            # Apply custom ScrapeOn theme
            ScrapeOnTheme.apply_theme()
            ctk.set_appearance_mode(app_config.APPEARANCE_MODE)
            ctk.set_default_color_theme(app_config.COLOR_THEME)
            
            if self.logger:
                self.logger.info(f"UI theme applied: {app_config.COLOR_THEME} ({app_config.APPEARANCE_MODE})")
                
        except Exception as e:
            print(f"Warning: Could not setup appearance: {e}")
            if self.logger:
                self.logger.error(f"Theme setup failed: {e}")
        
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        try:
            app_config.ensure_directories()
            if self.logger:
                self.logger.info("All required directories created/verified")
                
        except Exception as e:
            print(f"Error creating directories: {e}")
            if self.logger:
                self.logger.error(f"Directory creation failed: {e}")
            
    def initialize_database(self):
        """Initialize the database connection and setup"""
        try:
            self.db_manager = DatabaseManager(app_config.DATABASE_PATH)
            print("✅ Database initialized successfully")
            
            if self.logger:
                self.logger.info("Database initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize database: {e}"
            print(f"❌ {error_msg}")
            
            if self.logger:
                self.logger.critical(error_msg)
                
            import tkinter.messagebox as msgbox
            msgbox.showerror(
                "Database Error", 
                f"{error_msg}\n\nPlease check your installation and try again."
            )
            sys.exit(1)
        
    def show_login(self):
        """Show the login window"""
        try:
            if self.logger:
                self.logger.info("Showing login window")
                
            login_window = LoginWindow(
                self.on_login_success, 
                app_config.APP_NAME,
                web_config.get("web_api_url")
            )
            login_window.mainloop()
            
        except Exception as e:
            error_msg = f"Error showing login window: {e}"
            print(error_msg)
            
            if self.logger:
                self.logger.error(error_msg)
                
            sys.exit(1)
        
    def on_login_success(self, user):
        """Callback when user successfully logs in"""
        self.current_user = user
        print(f"✅ User {user.username} logged in successfully")
        
        if self.logger:
            self.logger.info(f"User login successful: {user.username} (Plan: {user.plan.name})")
            
        self.show_main_window()
        
    def show_main_window(self):
        """Show the main application window"""
        try:
            if self.logger:
                self.logger.info("Starting main application window")
                
            main_window = MainWindow(
                self.current_user, 
                app_config.APP_NAME,
                web_config.get("web_api_url")
            )
            main_window.mainloop()
            
        except Exception as e:
            error_msg = f"Error showing main window: {e}"
            print(error_msg)
            
            if self.logger:
                self.logger.error(error_msg)
                
            import tkinter.messagebox as msgbox
            msgbox.showerror("Application Error", f"Failed to start main application:\n{e}")
        
    def validate_environment(self):
        """Validate the application environment"""
        errors = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            errors.append("Python 3.8 or higher is required")
        
        # Validate configuration
        config_errors = app_config.validate_config()
        errors.extend(config_errors)
        
        # Check write permissions
        try:
            test_file = os.path.join(app_config.DATA_DIR, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            errors.append(f"No write permission in data directory: {e}")
        
        return errors
        
    def print_startup_info(self):
        """Print startup information"""
        print("=" * 60)
        print(f"🚀 Starting {app_config.APP_NAME} v{app_config.VERSION}")
        print(f"📝 {app_config.DESCRIPTION}")
        print("=" * 60)
        
        # Environment info
        env = os.environ.get('SCRAPEON_ENV', 'development').title()
        print(f"Environment: {env}")
        print(f"Python Version: {sys.version.split()[0]}")
        print(f"Database: {app_config.DATABASE_PATH}")
        
        # Web integration info
        if web_config.get("enable_web_sync"):
            print(f"Web API: {web_config.get('web_api_url')}")
            print(f"Website: {web_config.get('website_url')}")
        else:
            print("Web API: Disabled (Offline mode)")
        
        # Feature flags
        features = []
        if web_config.get("enable_web_sync"):
            features.append("Web Sync")
        if app_config.ENABLE_AUTO_UPDATES:
            features.append("Auto Updates")
        if app_config.ENABLE_ANALYTICS:
            features.append("Analytics")
        
        if features:
            print(f"Features: {', '.join(features)}")
        
        print("=" * 60)
        
    def run(self):
        """Start the application"""
        # Print startup information
        self.print_startup_info()
        
        # Validate environment
        validation_errors = self.validate_environment()
        if validation_errors:
            print("❌ Environment validation failed:")
            for error in validation_errors:
                print(f"   • {error}")
            
            if self.logger:
                self.logger.critical(f"Environment validation failed: {validation_errors}")
                
            sys.exit(1)
        
        print("✅ Environment validation passed")
        
        # Log configuration if in debug mode
        if self.logger and app_config.LOG_LEVEL == "DEBUG":
            app_config.print_config()
            
        # Start the application
        try:
            self.show_login()
            
        except KeyboardInterrupt:
            print("\n👋 Application closed by user")
            if self.logger:
                self.logger.info("Application closed by user (KeyboardInterrupt)")
                
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"❌ {error_msg}")
            
            if self.logger:
                self.logger.critical(error_msg, exc_info=True)
                
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            if self.logger:
                self.logger.info("Application shutdown")

def main():
    """Main entry point"""
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--version', '-v']:
            print(f"{app_config.APP_NAME} v{app_config.VERSION}")
            return
        elif sys.argv[1] in ['--help', '-h']:
            print(f"""
{app_config.APP_NAME} v{app_config.VERSION}
{app_config.DESCRIPTION}

Usage: python main.py [options]

Options:
  -h, --help     Show this help message
  -v, --version  Show version information
  --config       Show current configuration
  --validate     Validate environment and exit

Environment Variables:
  SCRAPEON_ENV   Set to 'production' for production mode (default: development)

Examples:
  python main.py                    # Run in development mode
  SCRAPEON_ENV=production python main.py  # Run in production mode
            """)
            return
        elif sys.argv[1] == '--config':
            app_config.print_config()
            return
        elif sys.argv[1] == '--validate':
            app = ScrapeOnApp()
            errors = app.validate_environment()
            if errors:
                print("❌ Validation failed:")
                for error in errors:
                    print(f"   • {error}")
                sys.exit(1)
            else:
                print("✅ Environment validation passed")
                sys.exit(0)
    
    # Create and run the application
    app = ScrapeOnApp()
    app.run()

if __name__ == "__main__":
    main()