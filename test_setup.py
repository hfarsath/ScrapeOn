# test_setup.py - Test if your ScrapeOn setup is working

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    try:
        import customtkinter as ctk
        print("✓ CustomTkinter imported successfully")
        
        import selenium
        print("✓ Selenium imported successfully")
        
        import pandas as pd
        print("✓ Pandas imported successfully")
        
        import requests
        print("✓ Requests imported successfully")
        
        from webdriver_manager.chrome import ChromeDriverManager
        print("✓ WebDriver Manager imported successfully")
        
        print("\n🎉 All packages imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_directories():
    """Test if required directories exist"""
    required_dirs = ['auth', 'scrapers', 'gui', 'utils', 'config', 'data', 'results']
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✓ Directory '{directory}' exists")
        else:
            print(f"❌ Directory '{directory}' missing")
            os.makedirs(directory, exist_ok=True)
            print(f"  → Created '{directory}' directory")

def test_simple_gui():
    """Test if CustomTkinter GUI can be created"""
    try:
        import customtkinter as ctk
        
        # Create a simple test window
        root = ctk.CTk()
        root.title("ScrapeOn - Setup Test")
        root.geometry("300x200")
        
        label = ctk.CTkLabel(root, text="ScrapeOn Setup Test")
        label.pack(pady=20)
        
        button = ctk.CTkButton(root, text="Close", command=root.destroy)
        button.pack(pady=10)
        
        print("✓ GUI test window created successfully")
        print("  → Close the test window to continue")
        
        root.mainloop()
        return True
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing ScrapeOn Setup...\n")
    
    print("1. Testing package imports...")
    imports_ok = test_imports()
    
    print("\n2. Testing directory structure...")
    test_directories()
    
    if imports_ok:
        print("\n3. Testing GUI creation...")
        gui_ok = test_simple_gui()
        
        if gui_ok:
            print("\n✅ ScrapeOn setup test completed successfully!")
            print("You can now run: python main.py")
        else:
            print("\n❌ GUI test failed. Check your CustomTkinter installation.")
    else:
        print("\n❌ Package import failed. Run: pip install -r requirements.txt")