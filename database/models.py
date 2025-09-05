# database/models.py
import sqlite3
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class User:
    def __init__(self, id=None, username=None, email=None, password_hash=None, 
                 full_name=None, plan_id=1, created_at=None, last_login=None, 
                 is_active=True, trial_end_date=None, subscription_end_date=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.plan_id = plan_id
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login
        self.is_active = is_active
        self.trial_end_date = trial_end_date
        self.subscription_end_date = subscription_end_date
        self.plan = None  # Will be loaded separately
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def is_plan_active(self):
        """Check if user's subscription is active"""
        now = datetime.utcnow()
        if self.trial_end_date and now <= self.trial_end_date:
            return True
        if self.subscription_end_date and now <= self.subscription_end_date:
            return True
        return False

class SubscriptionPlan:
    def __init__(self, id=None, name=None, description=None, monthly_scrapes=0,
                 max_results_per_scrape=0, price_monthly=0, price_yearly=0,
                 features=None, is_active=True):
        self.id = id
        self.name = name
        self.description = description
        self.monthly_scrapes = monthly_scrapes
        self.max_results_per_scrape = max_results_per_scrape
        self.price_monthly = price_monthly
        self.price_yearly = price_yearly
        self.features = features or "[]"
        self.is_active = is_active

class ScrapingSession:
    def __init__(self, id=None, user_id=None, scraper_type=None, query=None,
                 location=None, results_count=0, status='completed',
                 created_at=None, completed_at=None):
        self.id = id
        self.user_id = user_id
        self.scraper_type = scraper_type
        self.query = query
        self.location = location
        self.results_count = results_count
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.completed_at = completed_at

class DatabaseManager:
    def __init__(self, db_path="data/scrapeon.db"):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize database
        self.init_database()
        self.init_default_data()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Create database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create subscription_plans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscription_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    monthly_scrapes INTEGER NOT NULL,
                    max_results_per_scrape INTEGER NOT NULL,
                    price_monthly INTEGER DEFAULT 0,
                    price_yearly INTEGER DEFAULT 0,
                    features TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    plan_id INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    trial_end_date TIMESTAMP,
                    subscription_end_date TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
                )
            """)
            
            # Create scraping_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    scraper_type TEXT NOT NULL,
                    query TEXT NOT NULL,
                    location TEXT,
                    results_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def init_default_data(self):
        """Initialize default subscription plans and admin user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if plans already exist
            cursor.execute("SELECT COUNT(*) FROM subscription_plans")
            plan_count = cursor.fetchone()[0]
            
            if plan_count == 0:
                # Create default subscription plans
                plans = [
                    (1, "Free Trial", "7-day free trial with limited features", 50, 20, 0, 0, 
                     '["Basic scraping", "CSV export", "Email support"]'),
                    (2, "Basic", "Perfect for small businesses and individuals", 500, 100, 1999, 19990,
                     '["All scraping tools", "Excel/CSV export", "Priority support", "API access"]'),
                    (3, "Professional", "For growing businesses with higher needs", 2000, 500, 4999, 49990,
                     '["All Basic features", "Advanced filters", "Bulk export", "Custom integrations"]'),
                    (4, "Enterprise", "Unlimited scraping for large organizations", 999999, 999999, 9999, 99990,
                     '["All Professional features", "Unlimited scraping", "Custom development", "Dedicated support"]')
                ]
                
                cursor.executemany("""
                    INSERT INTO subscription_plans 
                    (id, name, description, monthly_scrapes, max_results_per_scrape, 
                     price_monthly, price_yearly, features)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, plans)
            
            # Check if admin user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("admin",))
            admin_count = cursor.fetchone()[0]
            
            if admin_count == 0:
                # Create admin user with enterprise plan
                admin_password_hash = hashlib.sha256("admin123".encode()).hexdigest()
                trial_end = datetime.utcnow() + timedelta(days=7)
                subscription_end = datetime.utcnow() + timedelta(days=3650)  # 10 years
                
                cursor.execute("""
                    INSERT INTO users 
                    (username, email, password_hash, full_name, plan_id, 
                     trial_end_date, subscription_end_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("admin", "admin@scrapeon.com", admin_password_hash, 
                      "System Administrator", 4, trial_end, subscription_end))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error initializing default data: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_user(self, username, email, password, full_name=None, plan_id=1):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user already exists
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE username = ? OR email = ?
            """, (username, email))
            
            if cursor.fetchone()[0] > 0:
                return None, "Username or email already exists"
            
            # Create new user with trial period
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            trial_end = datetime.utcnow() + timedelta(days=7)
            
            cursor.execute("""
                INSERT INTO users 
                (username, email, password_hash, full_name, plan_id, trial_end_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, email, password_hash, full_name, plan_id, trial_end))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Load and return the created user
            user = self.get_user_by_id(user_id)
            return user, "User created successfully"
            
        except Exception as e:
            conn.rollback()
            return None, f"Error creating user: {str(e)}"
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM users 
                WHERE username = ? AND is_active = 1
            """, (username,))
            
            user_row = cursor.fetchone()
            
            if user_row:
                # Convert row to User object
                user = self._row_to_user(user_row)
                
                if user.check_password(password):
                    # Update last login
                    cursor.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (user.id,))
                    conn.commit()
                    
                    # Load user's plan
                    user.plan = self.get_plan_by_id(user.plan_id)
                    
                    return user, "Login successful"
            
            return None, "Invalid credentials"
            
        except Exception as e:
            return None, f"Login error: {str(e)}"
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            
            if user_row:
                user = self._row_to_user(user_row)
                user.plan = self.get_plan_by_id(user.plan_id)
                return user
            
            return None
            
        finally:
            conn.close()
    
    def get_plan_by_id(self, plan_id):
        """Get subscription plan by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM subscription_plans WHERE id = ?", (plan_id,))
            plan_row = cursor.fetchone()
            
            if plan_row:
                return self._row_to_plan(plan_row)
            
            return None
            
        finally:
            conn.close()
    
    def get_all_plans(self):
        """Get all active subscription plans"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM subscription_plans WHERE is_active = 1 ORDER BY id")
            plan_rows = cursor.fetchall()
            
            return [self._row_to_plan(row) for row in plan_rows]
            
        finally:
            conn.close()
    
    def log_scraping_session(self, user_id, scraper_type, query, location=None, results_count=0):
        """Log a scraping session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO scraping_sessions 
                (user_id, scraper_type, query, location, results_count, completed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, scraper_type, query, location, results_count))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error logging scraping session: {e}")
        finally:
            conn.close()
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get user info
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Get current month stats
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            cursor.execute("""
                SELECT COUNT(*) FROM scraping_sessions 
                WHERE user_id = ? AND created_at >= ?
            """, (user_id, month_start))
            
            monthly_scrapes = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM scraping_sessions 
                WHERE user_id = ?
            """, (user_id,))
            
            total_scrapes = cursor.fetchone()[0]
            
            return {
                'user': user,
                'monthly_scrapes_used': monthly_scrapes,
                'monthly_scrapes_limit': user.plan.monthly_scrapes,
                'remaining_scrapes': max(0, user.plan.monthly_scrapes - monthly_scrapes),
                'total_scrapes_all_time': total_scrapes,
                'plan_active': user.is_plan_active(),
                'trial_end': user.trial_end_date,
                'subscription_end': user.subscription_end_date
            }
            
        finally:
            conn.close()
    
    def _row_to_user(self, row):
        """Convert database row to User object"""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            full_name=row['full_name'],
            plan_id=row['plan_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            is_active=bool(row['is_active']),
            trial_end_date=datetime.fromisoformat(row['trial_end_date']) if row['trial_end_date'] else None,
            subscription_end_date=datetime.fromisoformat(row['subscription_end_date']) if row['subscription_end_date'] else None
        )
    
    def _row_to_plan(self, row):
        """Convert database row to SubscriptionPlan object"""
        return SubscriptionPlan(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            monthly_scrapes=row['monthly_scrapes'],
            max_results_per_scrape=row['max_results_per_scrape'],
            price_monthly=row['price_monthly'],
            price_yearly=row['price_yearly'],
            features=row['features'],
            is_active=bool(row['is_active'])
        )