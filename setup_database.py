#!/usr/bin/env python3
"""
Database setup script for ScrapeOn
Run this script once to initialize the database with default plans and admin user
Uses only built-in Python libraries (no SQLAlchemy required)
"""

import os
import sys

def setup_database():
    """Initialize the database with default data"""
    print("Setting up ScrapeOn database...")
    print("Using SQLite with built-in Python libraries...")
    
    # Add the current directory to Python path so we can import our modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        from database.models import DatabaseManager
    except ImportError as e:
        print(f"Error: Could not import DatabaseManager.")
        print(f"Please make sure you have created the database/models.py file with the simplified version.")
        print(f"Import error: {e}")
        return False
    
    try:
        # Create data directory
        os.makedirs("data", exist_ok=True)
        
        # Initialize database
        print("Initializing database and tables...")
        db_manager = DatabaseManager()
        
        print("Database initialized successfully!")
        print("Default subscription plans created:")
        print("   - Free Trial (7 days, 50 scrapes/month)")
        print("   - Basic ($19.99/month, 500 scrapes/month)")
        print("   - Professional ($49.99/month, 2000 scrapes/month)")
        print("   - Enterprise ($99.99/month, unlimited scrapes)")
        print("Admin user created:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Plan: Enterprise (unlimited)")
        print("\nDatabase setup complete! You can now run the application.")
        print(f"Database file created at: {os.path.abspath('data/scrapeon.db')}")
        return True
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_database()
    if not success:
        print("\nSetup failed. Please check the error messages above.")
        print("Make sure you have created the database/models.py file with the simplified version.")
        sys.exit(1)