# auth/login.py - Updated for web integration
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import requests
import json
from database.models import DatabaseManager, User, SubscriptionPlan
from datetime import datetime

class LoginWindow(ctk.CTk):
    def __init__(self, login_callback, app_name="ScrapeOn", web_api_url=None):
        super().__init__()
        
        self.login_callback = login_callback
        self.app_name = app_name
        self.web_api_url = web_api_url or "http://localhost:8000/api"  # Your web API endpoint
        self.db_manager = DatabaseManager()
        
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """Configure the login window"""
        self.title(f"{self.app_name} - Desktop Client Login")
        self.geometry("450x600")
        self.resizable(False, False)
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"450x600+{x}+{y}")
        
    def create_widgets(self):
        """Create the login form widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text=f"{self.app_name}",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Desktop Client",
            font=ctk.CTkFont(size=16),
            text_color="#888888"
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Login form frame
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="x", padx=20, pady=20)
        
        form_title = ctk.CTkLabel(
            form_frame,
            text="Sign In to Your Account",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        form_title.pack(pady=(20, 20))
        
        # Username/Email field
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Username or Email",
            width=350,
            height=40
        )
        self.username_entry.pack(pady=10)
        
        # Password field
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Password",
            show="*",
            width=350,
            height=40
        )
        self.password_entry.pack(pady=10)
        
        # Login mode selection
        mode_frame = ctk.CTkFrame(form_frame)
        mode_frame.pack(pady=15)
        
        mode_label = ctk.CTkLabel(
            mode_frame,
            text="Login Mode:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        mode_label.pack(pady=(10, 5))
        
        self.login_mode = ctk.StringVar(value="web")
        
        web_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Web Account (Online)",
            variable=self.login_mode,
            value="web"
        )
        web_radio.pack(pady=2)
        
        local_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Local Account (Offline)",
            variable=self.login_mode,
            value="local"
        )
        local_radio.pack(pady=(2, 10))
        
        # Login button
        login_button = ctk.CTkButton(
            form_frame,
            text="Sign In",
            width=350,
            height=40,
            command=self.handle_login,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        login_button.pack(pady=20)
        
        # Web registration info
        web_info_frame = ctk.CTkFrame(main_frame)
        web_info_frame.pack(fill="x", padx=20, pady=10)
        
        web_info_title = ctk.CTkLabel(
            web_info_frame,
            text="New User?",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        web_info_title.pack(pady=(15, 5))
        
        web_info_text = ctk.CTkLabel(
            web_info_frame,
            text="Register for a new account on our website:",
            font=ctk.CTkFont(size=12)
        )
        web_info_text.pack(pady=2)
        
        website_button = ctk.CTkButton(
            web_info_frame,
            text="Visit ScrapeOn.com",
            width=200,
            height=30,
            command=self.open_website,
            fg_color="transparent",
            border_width=2
        )
        website_button.pack(pady=(5, 15))
        
        # Demo credentials
        demo_frame = ctk.CTkFrame(main_frame)
        demo_frame.pack(fill="x", padx=20, pady=10)
        
        demo_title = ctk.CTkLabel(
            demo_frame,
            text="Demo Credentials (Local)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        demo_title.pack(pady=(15, 5))
        
        demo_creds = ctk.CTkLabel(
            demo_frame,
            text="Username: admin\nPassword: admin123",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        demo_creds.pack(pady=(0, 15))
        
        # Bind Enter key to login
        self.bind('<Return>', lambda event: self.handle_login())
        
    def open_website(self):
        """Open registration website"""
        import webbrowser
        webbrowser.open("https://scrapeon.com/register")  # Replace with your actual website
        
    def handle_login(self):
        """Handle login button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        mode = self.login_mode.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username/email and password")
            return
        
        if mode == "web":
            self.handle_web_login(username, password)
        else:
            self.handle_local_login(username, password)
        
    def handle_web_login(self, username, password):
        """Handle web-based authentication"""
        try:
            # Show loading state
            self.configure(cursor="wait")
            
            # Make API request to web backend
            response = requests.post(
                f"{self.web_api_url}/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Sync user data to local database
                user = self.sync_user_from_web(user_data)
                
                if user:
                    messagebox.showinfo("Success", f"Welcome back, {user.full_name or user.username}!")
                    self.destroy()
                    self.login_callback(user)
                else:
                    messagebox.showerror("Error", "Failed to sync user data")
                    
            elif response.status_code == 401:
                messagebox.showerror("Login Failed", "Invalid credentials")
            elif response.status_code == 403:
                messagebox.showerror("Account Suspended", "Your account has been suspended. Please contact support.")
            else:
                messagebox.showerror("Login Failed", f"Server error: {response.status_code}")
                
        except requests.ConnectionError:
            messagebox.showerror(
                "Connection Error", 
                "Cannot connect to web server. Please check your internet connection or try local login."
            )
        except requests.Timeout:
            messagebox.showerror("Timeout", "Login request timed out. Please try again.")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
        finally:
            self.configure(cursor="")
    
    def handle_local_login(self, username, password):
        """Handle local database authentication"""
        user, message = self.db_manager.authenticate_user(username, password)
        
        if user:
            messagebox.showinfo("Success", f"Welcome back, {user.full_name or user.username}!")
            self.destroy()
            self.login_callback(user)
        else:
            messagebox.showerror("Login Failed", message)
    
    def sync_user_from_web(self, user_data):
        """Sync user data from web API to local database"""
        try:
            # Check if user exists locally
            local_user = None
            if 'id' in user_data:
                # Try to find by web_user_id if you store it
                pass
            
            # Try to find by username or email
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM users 
                WHERE username = ? OR email = ?
            """, (user_data.get('username'), user_data.get('email')))
            
            user_row = cursor.fetchone()
            
            if user_row:
                # Update existing user
                cursor.execute("""
                    UPDATE users SET 
                        email = ?, full_name = ?, plan_id = ?, 
                        subscription_end_date = ?, last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    user_data.get('email'),
                    user_data.get('full_name'),
                    self.map_web_plan_to_local(user_data.get('plan')),
                    user_data.get('subscription_end_date'),
                    user_row['id']
                ))
                user_id = user_row['id']
            else:
                # Create new user locally
                cursor.execute("""
                    INSERT INTO users 
                    (username, email, password_hash, full_name, plan_id, 
                     subscription_end_date, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    user_data.get('username'),
                    user_data.get('email'),
                    'web_authenticated',  # Placeholder since web handles auth
                    user_data.get('full_name'),
                    self.map_web_plan_to_local(user_data.get('plan')),
                    user_data.get('subscription_end_date')
                ))
                user_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            # Return the user object
            return self.db_manager.get_user_by_id(user_id)
            
        except Exception as e:
            print(f"Error syncing user: {e}")
            return None
    
    def map_web_plan_to_local(self, web_plan):
        """Map web plan name to local plan ID"""
        plan_mapping = {
            'free_trial': 1,
            'basic': 2,
            'professional': 3,
            'enterprise': 4
        }
        return plan_mapping.get(web_plan, 1)

class OfflineOnlyWindow(ctk.CTkToplevel):
    """Window shown when certain features require online access"""
    def __init__(self, parent, feature_name):
        super().__init__(parent)
        
        self.feature_name = feature_name
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """Configure the window"""
        self.title("Online Feature")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient()
        self.grab_set()
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"400x300+{x}+{y}")
        
    def create_widgets(self):
        """Create the widgets"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Online Feature",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(30, 20))
        
        message_label = ctk.CTkLabel(
            main_frame,
            text=f"The {self.feature_name} feature requires an online account.\n\nPlease log in with your web account or visit our website to register.",
            font=ctk.CTkFont(size=14),
            wraplength=300
        )
        message_label.pack(pady=20)
        
        website_button = ctk.CTkButton(
            main_frame,
            text="Visit Website",
            width=200,
            height=40,
            command=self.open_website
        )
        website_button.pack(pady=10)
        
        close_button = ctk.CTkButton(
            main_frame,
            text="Close",
            width=200,
            height=40,
            command=self.destroy,
            fg_color="transparent",
            border_width=2
        )
        close_button.pack(pady=10)
        
    def open_website(self):
        """Open website"""
        import webbrowser
        webbrowser.open("https://scrapeon.com")  # Replace with your actual website
        self.destroy()