# config/theme.py
import customtkinter as ctk

class ScrapeOnTheme:
    """Custom theme configuration for ScrapeOn"""
    
    # Primary color: #031ea6
    PRIMARY_BLUE = "#031ea6"
    PRIMARY_BLUE_HOVER = "#0429cc"
    PRIMARY_BLUE_DARK = "#021459"
    
    # Secondary colors
    SECONDARY_BLUE = "#1e3a8a"
    LIGHT_BLUE = "#3b82f6"
    
    # Neutral colors
    DARK_BG = "#1a1a1a"
    MEDIUM_BG = "#2b2b2b"
    LIGHT_BG = "#3c3c3c"
    
    # Text colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#cccccc"
    TEXT_MUTED = "#888888"
    
    # Status colors
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    
    @classmethod
    def apply_theme(cls):
        """Apply the custom theme to CustomTkinter"""
        # Set appearance mode
        ctk.set_appearance_mode("dark")
        
        # Create custom color theme
        custom_theme = {
            "CTk": {
                "fg_color": [cls.DARK_BG, cls.DARK_BG]
            },
            "CTkToplevel": {
                "fg_color": [cls.DARK_BG, cls.DARK_BG]
            },
            "CTkFrame": {
                "fg_color": [cls.MEDIUM_BG, cls.MEDIUM_BG],
                "border_color": [cls.PRIMARY_BLUE, cls.PRIMARY_BLUE]
            },
            "CTkButton": {
                "fg_color": [cls.PRIMARY_BLUE, cls.PRIMARY_BLUE],
                "hover_color": [cls.PRIMARY_BLUE_HOVER, cls.PRIMARY_BLUE_HOVER],
                "border_color": [cls.PRIMARY_BLUE, cls.PRIMARY_BLUE],
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY]
            },
            "CTkLabel": {
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY]
            },
            "CTkEntry": {
                "fg_color": [cls.LIGHT_BG, cls.LIGHT_BG],
                "border_color": [cls.PRIMARY_BLUE, cls.PRIMARY_BLUE],
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY],
                "placeholder_text_color": [cls.TEXT_MUTED, cls.TEXT_MUTED]
            },
            "CTkTextbox": {
                "fg_color": [cls.LIGHT_BG, cls.LIGHT_BG],
                "border_color": [cls.PRIMARY_BLUE, cls.PRIMARY_BLUE],
                "text_color": [cls.TEXT_PRIMARY, cls.TEXT_PRIMARY]
            },
            "CTkScrollbar": {
                "fg_color": [cls.MEDIUM_BG, cls.MEDIUM_BG],
                "button_color": [cls.PRIMARY_BLUE, cls.PRIMARY_BLUE],
                "button_hover_color": [cls.PRIMARY_BLUE_HOVER, cls.PRIMARY_BLUE_HOVER]
            },
            "CTkProgressBar": {
                "fg_color": [cls.MEDIUM_BG, cls.MEDIUM_BG],
                "progress_color": [cls.PRIMARY_BLUE, cls.PRIMARY_BLUE]
            }
        }
        
        # Apply the theme (Note: This is a conceptual approach)
        # CustomTkinter doesn't support runtime theme creation, so we'll use configure methods
        return custom_theme
    
    @classmethod
    def configure_button(cls, button, style="primary"):
        """Configure button with custom colors"""
        if style == "primary":
            button.configure(
                fg_color=cls.PRIMARY_BLUE,
                hover_color=cls.PRIMARY_BLUE_HOVER,
                border_color=cls.PRIMARY_BLUE
            )
        elif style == "secondary":
            button.configure(
                fg_color="transparent",
                hover_color=cls.PRIMARY_BLUE_DARK,
                border_color=cls.PRIMARY_BLUE,
                border_width=2
            )
        elif style == "success":
            button.configure(
                fg_color=cls.SUCCESS,
                hover_color="#059669"
            )
        elif style == "warning":
            button.configure(
                fg_color=cls.WARNING,
                hover_color="#d97706"
            )
        elif style == "danger":
            button.configure(
                fg_color=cls.ERROR,
                hover_color="#dc2626"
            )
    
    @classmethod
    def configure_frame(cls, frame, style="default"):
        """Configure frame with custom colors"""
        if style == "primary":
            frame.configure(
                fg_color=cls.PRIMARY_BLUE_DARK,
                border_color=cls.PRIMARY_BLUE,
                border_width=2
            )
        elif style == "secondary":
            frame.configure(
                fg_color=cls.MEDIUM_BG,
                border_color=cls.PRIMARY_BLUE,
                border_width=1
            )
        else:
            frame.configure(
                fg_color=cls.MEDIUM_BG,
                border_color=cls.PRIMARY_BLUE
            )