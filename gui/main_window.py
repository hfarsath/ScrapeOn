# gui/main_window.py - Updated for web integration
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from config.theme import ScrapeOnTheme
from scrapers.google_maps import GoogleMapsScraper
from scrapers.email_scraper import EmailScraper
from scrapers.phone_scraper import PhoneScraper
from database.models import DatabaseManager
import threading
import os
import time
import requests
import webbrowser

class MainWindow(ctk.CTk):
    def __init__(self, user, app_name="ScrapeOn", web_api_url=None):
        super().__init__()
        
        self.user = user
        self.app_name = app_name
        self.web_api_url = web_api_url or "http://localhost:8000/api"
        self.current_scraper = None
        self.db_manager = DatabaseManager()
        
        self.setup_window()
        self.create_widgets()
        self.check_user_limits()
        
    def setup_window(self):
        """Configure the main window"""
        self.title(f"{self.app_name} - Welcome {self.user.full_name or self.user.username}")
        self.geometry("1000x750")
        self.minsize(900, 650)
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"1000x750+{x}+{y}")
        
    def create_widgets(self):
        """Create the main application widgets"""
        # Header frame
        header_frame = ctk.CTkFrame(self, height=90)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        # Left side - Title and plan info
        left_header = ctk.CTkFrame(header_frame)
        left_header.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            left_header,
            text=self.app_name,
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(side="left", padx=20)
        
        plan_label = ctk.CTkLabel(
            left_header,
            text=f"Plan: {self.user.plan.name}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ScrapeOnTheme.SUCCESS if self.user.is_plan_active() else ScrapeOnTheme.ERROR
        )
        plan_label.pack(side="left", padx=20)
        
        # Account type indicator
        account_type = "Web Account" if self.is_web_user() else "Local Account"
        account_label = ctk.CTkLabel(
            left_header,
            text=f"({account_type})",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        account_label.pack(side="left", padx=10)
        
        # Right side - User info and actions
        right_header = ctk.CTkFrame(header_frame)
        right_header.pack(side="right", fill="y", padx=10, pady=10)
        
        user_label = ctk.CTkLabel(
            right_header,
            text=f"Welcome, {self.user.full_name or self.user.username}",
            font=ctk.CTkFont(size=14)
        )
        user_label.pack(side="top", padx=20, pady=(10, 5))
        
        # User actions frame
        actions_frame = ctk.CTkFrame(right_header)
        actions_frame.pack(side="bottom", padx=10, pady=5)
        
        # Web dashboard button (only for web users)
        if self.is_web_user():
            dashboard_button = ctk.CTkButton(
                actions_frame,
                text="Dashboard",
                width=80,
                height=30,
                command=self.open_web_dashboard,
                font=ctk.CTkFont(size=12)
            )
            dashboard_button.pack(side="left", padx=5)
        
        profile_button = ctk.CTkButton(
            actions_frame,
            text="Profile",
            width=80,
            height=30,
            command=self.show_profile,
            font=ctk.CTkFont(size=12)
        )
        profile_button.pack(side="left", padx=5)
        
        logout_button = ctk.CTkButton(
            actions_frame,
            text="Logout",
            width=80,
            height=30,
            command=self.logout,
            fg_color=ScrapeOnTheme.ERROR,
            hover_color="#dc2626",
            font=ctk.CTkFont(size=12)
        )
        logout_button.pack(side="left", padx=5)
        
        # Usage stats frame
        self.usage_frame = ctk.CTkFrame(self, height=60)
        self.usage_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.usage_frame.pack_propagate(False)
        
        self.update_usage_display()
        
        # Main content frame
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Left sidebar for scraper selection
        sidebar = ctk.CTkFrame(content_frame, width=220)
        sidebar.pack(side="left", fill="y", padx=(20, 10), pady=20)
        sidebar.pack_propagate(False)
        
        sidebar_title = ctk.CTkLabel(
            sidebar,
            text="Scraping Tools",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        sidebar_title.pack(pady=(20, 30))
        
        # Scraper buttons
        self.maps_button = ctk.CTkButton(
            sidebar,
            text="🗺️ Google Maps\nScraper",
            width=180,
            height=60,
            command=self.show_maps_scraper,
            fg_color=ScrapeOnTheme.PRIMARY_BLUE,
            hover_color=ScrapeOnTheme.PRIMARY_BLUE_HOVER
        )
        self.maps_button.pack(pady=10)
        
        self.email_button = ctk.CTkButton(
            sidebar,
            text="📧 Email\nScraper",
            width=180,
            height=60,
            command=self.show_email_scraper,
            fg_color=ScrapeOnTheme.PRIMARY_BLUE,
            hover_color=ScrapeOnTheme.PRIMARY_BLUE_HOVER
        )
        self.email_button.pack(pady=10)
        
        self.phone_button = ctk.CTkButton(
            sidebar,
            text="📞 Phone\nScraper",
            width=180,
            height=60,
            command=self.show_phone_scraper,
            fg_color=ScrapeOnTheme.PRIMARY_BLUE,
            hover_color=ScrapeOnTheme.PRIMARY_BLUE_HOVER
        )
        self.phone_button.pack(pady=10)
        
        # Account management buttons
        if self.is_web_user():
            # For web users - link to web dashboard
            manage_button = ctk.CTkButton(
                sidebar,
                text="💳 Manage Plan",
                width=180,
                height=40,
                command=self.open_billing_page,
                fg_color=ScrapeOnTheme.WARNING,
                hover_color="#d97706"
            )
            manage_button.pack(pady=20)
        else:
            # For local users - show upgrade prompt
            if not self.user.is_plan_active() or self.user.plan.name == "Free Trial":
                upgrade_button = ctk.CTkButton(
                    sidebar,
                    text="⭐ Get Web Account",
                    width=180,
                    height=40,
                    command=self.show_web_signup_prompt,
                    fg_color=ScrapeOnTheme.WARNING,
                    hover_color="#d97706"
                )
                upgrade_button.pack(pady=20)
        
        # Right content area
        self.content_area = ctk.CTkFrame(content_frame)
        self.content_area.pack(side="right", expand=True, fill="both", padx=(10, 20), pady=20)
        
        # Default welcome content
        self.show_welcome_content()
    
    def is_web_user(self):
        """Check if user is authenticated via web"""
        return self.user.password_hash == 'web_authenticated'
    
    def open_web_dashboard(self):
        """Open web dashboard"""
        webbrowser.open("https://scrapeon.com/dashboard")  # Replace with your actual dashboard URL
    
    def open_billing_page(self):
        """Open billing/subscription management page"""
        webbrowser.open("https://scrapeon.com/billing")  # Replace with your actual billing URL
    
    def show_web_signup_prompt(self):
        """Show prompt to create web account"""
        WebSignupPromptWindow(self)
    
    def sync_usage_with_web(self):
        """Sync usage data with web backend"""
        if not self.is_web_user():
            return
        
        try:
            # Get local usage data
            stats = self.db_manager.get_user_stats(self.user.id)
            
            # Send to web backend
            requests.post(
                f"{self.web_api_url}/usage/sync",
                json={
                    "user_id": self.user.username,  # or however you identify users
                    "monthly_scrapes": stats['monthly_scrapes_used']
                },
                timeout=5
            )
        except:
            # Fail silently - offline mode
            pass
    
    def update_usage_display(self):
        """Update the usage statistics display"""
        # Clear existing widgets
        for widget in self.usage_frame.winfo_children():
            widget.destroy()
        
        # Get current stats
        stats = self.db_manager.get_user_stats(self.user.id)
        if not stats:
            return
        
        # Sync with web if web user
        if self.is_web_user():
            self.sync_usage_with_web()
        
        # Usage info
        usage_label = ctk.CTkLabel(
            self.usage_frame,
            text=f"Monthly Usage: {stats['monthly_scrapes_used']} / {stats['monthly_scrapes_limit']} scrapes",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        usage_label.pack(side="left", padx=20, pady=15)
        
        # Progress bar
        if stats['monthly_scrapes_limit'] > 0:
            progress_value = min(1.0, stats['monthly_scrapes_used'] / stats['monthly_scrapes_limit'])
            progress_bar = ctk.CTkProgressBar(self.usage_frame, width=300)
            progress_bar.pack(side="left", padx=20, pady=15)
            progress_bar.set(progress_value)
            
            # Color based on usage
            if progress_value < 0.7:
                color = "#10b981"  # Green
            elif progress_value < 0.9:
                color = "#f59e0b"  # Yellow
            else:
                color = "#ef4444"  # Red
            progress_bar.configure(progress_color=color)
        
        # Remaining scrapes
        remaining_label = ctk.CTkLabel(
            self.usage_frame,
            text=f"Remaining: {stats['remaining_scrapes']} scrapes",
            font=ctk.CTkFont(size=12)
        )
        remaining_label.pack(side="right", padx=20, pady=15)
        
        # Sync indicator for web users
        if self.is_web_user():
            sync_label = ctk.CTkLabel(
                self.usage_frame,
                text="🌐 Synced",
                font=ctk.CTkFont(size=10),
                text_color="#10b981"
            )
            sync_label.pack(side="right", padx=5, pady=15)
    
    def check_user_limits(self):
        """Check if user has reached their limits"""
        stats = self.db_manager.get_user_stats(self.user.id)
        
        if not stats or not stats['plan_active']:
            # Different messages for web vs local users
            if self.is_web_user():
                message = "Your subscription has expired. Please visit your web dashboard to renew."
            else:
                message = "Your trial has expired. Please create a web account for continued access."
            self.disable_scraping_buttons(message)
            return False
        
        if stats['remaining_scrapes'] <= 0:
            # Different messages for web vs local users
            if self.is_web_user():
                message = "You've reached your monthly limit. Upgrade your plan in the web dashboard."
            else:
                message = "You've reached your monthly limit. Create a web account for higher limits."
            self.disable_scraping_buttons(message)
            return False
        
        return True
    
    def disable_scraping_buttons(self, message):
        """Disable all scraping buttons and show message"""
        self.maps_button.configure(state="disabled")
        self.email_button.configure(state="disabled")
        self.phone_button.configure(state="disabled")
        
        # Show warning in content area
        self.clear_content_area()
        
        warning_label = ctk.CTkLabel(
            self.content_area,
            text="⚠️ Scraping Limit Reached",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=ScrapeOnTheme.ERROR
        )
        warning_label.pack(pady=(100, 20))
        
        message_label = ctk.CTkLabel(
            self.content_area,
            text=message,
            font=ctk.CTkFont(size=16),
            wraplength=400
        )
        message_label.pack(pady=20)
        
        # Different action buttons based on user type
        if self.is_web_user():
            dashboard_button = ctk.CTkButton(
                self.content_area,
                text="Open Web Dashboard",
                width=200,
                height=50,
                command=self.open_web_dashboard,
                fg_color=ScrapeOnTheme.WARNING,
                hover_color="#d97706",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            dashboard_button.pack(pady=30)
        else:
            signup_button = ctk.CTkButton(
                self.content_area,
                text="Create Web Account",
                width=200,
                height=50,
                command=self.show_web_signup_prompt,
                fg_color=ScrapeOnTheme.WARNING,
                hover_color="#d97706",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            signup_button.pack(pady=30)
    
    def show_profile(self):
        """Show user profile window"""
        if self.is_web_user():
            # For web users, show limited profile or redirect to web
            WebUserProfileWindow(self, self.user)
        else:
            # For local users, show full local profile
            try:
                from auth.login import UserProfileWindow
                UserProfileWindow(self, self.user)
            except ImportError:
                messagebox.showinfo("Profile", f"User: {self.user.username}\nPlan: {self.user.plan.name}")
    
    def logout(self):
        """Handle logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()
            # Restart the login process
            from auth.login import LoginWindow
            login_window = LoginWindow(lambda user: MainWindow(user).mainloop(), self.app_name)
            login_window.mainloop()
    
    def log_scraping_activity(self, scraper_type, query, location, results_count):
        """Log scraping activity to database and sync with web if needed"""
        # Log locally
        self.db_manager.log_scraping_session(
            user_id=self.user.id,
            scraper_type=scraper_type,
            query=query,
            location=location,
            results_count=results_count
        )
        
        # Sync with web backend if web user
        if self.is_web_user():
            try:
                requests.post(
                    f"{self.web_api_url}/scraping/log",
                    json={
                        "user_id": self.user.username,
                        "scraper_type": scraper_type,
                        "query": query,
                        "location": location,
                        "results_count": results_count
                    },
                    timeout=5
                )
            except:
                # Continue offline if web sync fails
                pass
        
        # Update usage display
        self.update_usage_display()
    
    def clear_content_area(self):
        """Clear the content area"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
    def show_welcome_content(self):
        """Show welcome message in content area"""
        self.clear_content_area()
        
        welcome_label = ctk.CTkLabel(
            self.content_area,
            text=f"Welcome to {self.app_name}!",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        welcome_label.pack(pady=(50, 20))
        
        # Show account-specific welcome message
        if self.is_web_user():
            web_label = ctk.CTkLabel(
                self.content_area,
                text="Connected to your web account",
                font=ctk.CTkFont(size=16),
                text_color=ScrapeOnTheme.SUCCESS
            )
            web_label.pack(pady=10)
        else:
            if self.user.plan.name == "Free Trial":
                trial_label = ctk.CTkLabel(
                    self.content_area,
                    text="Using local demo account",
                    font=ctk.CTkFont(size=16),
                    text_color="#888888"
                )
                trial_label.pack(pady=10)
        
        instruction_label = ctk.CTkLabel(
            self.content_area,
            text="Select a scraping tool from the sidebar to get started.",
            font=ctk.CTkFont(size=16)
        )
        instruction_label.pack(pady=10)
        
        # Features based on plan
        features_frame = ctk.CTkFrame(self.content_area)
        features_frame.pack(pady=30, padx=50, fill="x")
        
        features_title = ctk.CTkLabel(
            features_frame,
            text="Your Plan Features:",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        features_title.pack(pady=(20, 15))
        
        # Show plan-specific features
        import json
        try:
            features = json.loads(self.user.plan.features or '[]')
        except:
            features = ["Basic scraping tools", "CSV export", "Email support"]
        
        for feature in features:
            feature_label = ctk.CTkLabel(
                features_frame,
                text=f"✅ {feature}",
                font=ctk.CTkFont(size=14)
            )
            feature_label.pack(pady=5, anchor="w", padx=20)
        
        # Usage summary
        stats = self.db_manager.get_user_stats(self.user.id)
        if stats:
            usage_info = ctk.CTkLabel(
                features_frame,
                text=f"\n📊 Usage This Month: {stats['monthly_scrapes_used']} / {stats['monthly_scrapes_limit']} scrapes",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            usage_info.pack(pady=(15, 20))
    
    # Include all the scraping methods from the previous complete main window
    # (show_maps_scraper, show_email_scraper, show_phone_scraper, etc.)
    # For brevity, I'll include key methods only
    
    def show_maps_scraper(self):
        """Show Google Maps scraper interface"""
        if not self.check_user_limits():
            return
        # ... (rest of the method as in complete_main_window)
    
    def show_email_scraper(self):
        """Show email scraper interface"""  
        if not self.check_user_limits():
            return
        # ... (rest of the method as in complete_main_window)
    
    def show_phone_scraper(self):
        """Show phone scraper interface"""
        if not self.check_user_limits():
            return
        # ... (rest of the method as in complete_main_window)
    
    def highlight_button(self, active_button):
        """Highlight the active scraper button"""
        buttons = [self.maps_button, self.email_button, self.phone_button]
        for button in buttons:
            if button == active_button:
                button.configure(fg_color=ScrapeOnTheme.PRIMARY_BLUE_HOVER)
            else:
                button.configure(fg_color=ScrapeOnTheme.PRIMARY_BLUE)


class WebUserProfileWindow(ctk.CTkToplevel):
    """Profile window for web users with limited local info"""
    def __init__(self, parent, user):
        super().__init__(parent)
        
        self.parent = parent
        self.user = user
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """Configure the profile window"""
        self.title("Profile - Web Account")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(self.parent)
        self.grab_set()
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"500x400+{x}+{y}")
        
    def create_widgets(self):
        """Create the profile widgets"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Web Account Profile",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Basic info frame
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_details = [
            ("Username:", self.user.username),
            ("Email:", self.user.email),
            ("Plan:", self.user.plan.name),
            ("Account Type:", "Web Account")
        ]
        
        for label, value in info_details:
            detail_frame = ctk.CTkFrame(info_frame)
            detail_frame.pack(fill="x", padx=20, pady=5)
            
            label_widget = ctk.CTkLabel(
                detail_frame,
                text=label,
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            )
            label_widget.pack(side="left", padx=10, pady=10)
            
            value_widget = ctk.CTkLabel(
                detail_frame,
                text=value,
                anchor="e"
            )
            value_widget.pack(side="right", padx=10, pady=10)
        
        # Web dashboard button
        dashboard_button = ctk.CTkButton(
            main_frame,
            text="Open Web Dashboard",
            width=250,
            height=40,
            command=self.open_dashboard,
            fg_color=ScrapeOnTheme.PRIMARY_BLUE,
            hover_color=ScrapeOnTheme.PRIMARY_BLUE_HOVER
        )
        dashboard_button.pack(pady=20)
        
        # Info text
        info_label = ctk.CTkLabel(
            main_frame,
            text="For detailed account management, billing,\nand advanced features, use the web dashboard.",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        info_label.pack(pady=10)
        
        # Close button
        close_button = ctk.CTkButton(
            main_frame,
            text="Close",
            width=200,
            height=40,
            command=self.destroy
        )
        close_button.pack(pady=20)
        
    def open_dashboard(self):
        """Open web dashboard"""
        import webbrowser
        webbrowser.open("https://scrapeon.com/dashboard")  # Replace with your actual dashboard URL
        self.destroy()


class WebSignupPromptWindow(ctk.CTkToplevel):
    """Window to prompt local users to create web accounts"""
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """Configure the window"""
        self.title("Upgrade to Web Account")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(self.parent)
        self.grab_set()
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"500x600+{x}+{y}")
        
    def create_widgets(self):
        """Create the widgets"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Upgrade to Web Account",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(30, 20))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Get more features with a web account",
            font=ctk.CTkFont(size=16),
            text_color="#888888"
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Benefits frame
        benefits_frame = ctk.CTkFrame(main_frame)
        benefits_frame.pack(fill="x", padx=20, pady=20)
        
        benefits_title = ctk.CTkLabel(
            benefits_frame,
            text="Web Account Benefits:",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        benefits_title.pack(pady=(20, 15))
        
        benefits = [
            "Higher monthly scraping limits",
            "Multiple subscription plans",
            "Cloud data synchronization",
            "Web dashboard access",
            "Priority customer support",
            "Advanced analytics and reporting",
            "API access for integrations",
            "Team collaboration features"
        ]
        
        for benefit in benefits:
            benefit_label = ctk.CTkLabel(
                benefits_frame,
                text=f"✅ {benefit}",
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            benefit_label.pack(pady=3, anchor="w", padx=20)
        
        benefits_frame.pack(pady=(0, 20), padx=20)
        
        # Action buttons
        signup_button = ctk.CTkButton(
            main_frame,
            text="Create Web Account",
            width=300,
            height=50,
            command=self.open_signup,
            fg_color=ScrapeOnTheme.SUCCESS,
            hover_color="#059669",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        signup_button.pack(pady=20)
        
        close_button = ctk.CTkButton(
            main_frame,
            text="Maybe Later",
            width=300,
            height=40,
            command=self.destroy,
            fg_color="transparent",
            border_width=2
        )
        close_button.pack(pady=10)
        
    def open_signup(self):
        """Open signup page"""
        import webbrowser
        webbrowser.open("https://scrapeon.com/register")  # Replace with your actual signup URL
        self.destroy()