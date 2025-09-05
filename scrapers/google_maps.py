# scrapers/google_maps.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import pandas as pd
import time
import re
from urllib.parse import quote
import json
import os

class GoogleMapsScraper:
    def __init__(self):
        self.driver = None
        self.results = []
        
    def setup_driver(self, headless=False):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if headless:
            chrome_options.add_argument("--headless")
        
        try:
            # Use WebDriver Manager to automatically download ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return False
        
    def scrape(self, query, location="", max_results=20, progress_callback=None):
        """Scrape Google Maps for business information"""
        self.results = []
        
        if not self.setup_driver():
            if progress_callback:
                progress_callback("❌ Error: Could not setup Chrome driver")
            return []
        
        try:
            # Build search query
            search_query = f"{query}"
            if location:
                search_query += f" in {location}"
                
            if progress_callback:
                progress_callback(f"🔍 Searching for: {search_query}")
            
            # Navigate to Google Maps
            maps_url = f"https://www.google.com/maps/search/{quote(search_query)}"
            self.driver.get(maps_url)
            
            # Wait for page to load
            time.sleep(5)
            
            if progress_callback:
                progress_callback("📍 Page loaded. Looking for results...")
            
            # Wait for results to appear
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[role='main']"))
                )
            except:
                if progress_callback:
                    progress_callback("⚠️ No results found or page didn't load properly")
                return []
            
            # Scroll and collect results
            self.scroll_and_collect_results(max_results, progress_callback)
            
            if progress_callback:
                progress_callback(f"✅ Scraping completed! Found {len(self.results)} results")
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Error during scraping: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                
        return self.results
        
    def scroll_and_collect_results(self, max_results, progress_callback, stop_callback=None):
        """Scroll through results and collect business data"""
        try:
            # Convert max_results to int to avoid comparison issues
            max_results = int(max_results)
            
            # Find the scrollable results panel
            results_panel = self.driver.find_element(By.CSS_SELECTOR, "[role='main']")
            
            collected_names = set()  # Track unique business names
            scroll_attempts = 0
            max_scroll_attempts = 10
            
            while len(self.results) < max_results and scroll_attempts < max_scroll_attempts:
                # Check for stop signal
                if stop_callback and stop_callback():
                    if progress_callback:
                        progress_callback("Scraping stopped by user")
                    break
                
                try:
                    # Find business listings using multiple selectors
                    business_elements = []
                    
                    # Try different selectors for business listings
                    selectors = [
                        "[data-result-index]",
                        ".hfpxzc",
                        "a[href*='/maps/place/']",
                        "[jsaction*='mouseover']"
                    ]
                    
                    for selector in selectors:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            business_elements = elements
                            break
                    
                    if not business_elements:
                        if progress_callback:
                            progress_callback("⚠️ No business elements found on page")
                        break
                    
                    if progress_callback:
                        progress_callback(f"🔍 Found {len(business_elements)} potential businesses on page")
                    
                    # Process each business element
                    for i, element in enumerate(business_elements):
                        # Check for stop signal in inner loop too
                        if stop_callback and stop_callback():
                            if progress_callback:
                                progress_callback("Scraping stopped by user")
                            return
                            
                        if len(self.results) >= max_results:
                            break
                            
                        try:
                            # Scroll element into view
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)
                            
                            # Click on the business to get details
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(3)  # Wait for details to load
                            
                            # Extract business data
                            business_data = self.extract_business_data()
                            
                            if business_data and business_data.get('name'):
                                # Check if we already have this business
                                if business_data['name'] not in collected_names:
                                    collected_names.add(business_data['name'])
                                    self.results.append(business_data)
                                    
                                    if progress_callback:
                                        progress_callback(f"📋 Extracted: {business_data['name']} ({len(self.results)}/{max_results})")
                                else:
                                    if progress_callback:
                                        progress_callback(f"🔄 Duplicate found: {business_data['name']}")
                        
                        except Exception as e:
                            if progress_callback:
                                progress_callback(f"⚠️ Error processing business {i+1}: {str(e)}")
                            continue
                    
                    # Check if we need more results
                    if len(self.results) < max_results:
                        # Scroll down to load more results
                        self.driver.execute_script("arguments[0].scrollBy(0, 1000);", results_panel)
                        time.sleep(3)
                        scroll_attempts += 1
                        
                        if progress_callback:
                            progress_callback(f"📜 Scrolling for more results... (Attempt {scroll_attempts}/{max_scroll_attempts})")
                    else:
                        break
                        
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"❌ Error in scroll loop: {str(e)}")
                    break
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Error collecting results: {str(e)}")
            print(f"Detailed error: {e}")  # For debugging
    
    def extract_business_data(self):
        """Extract business data from the current view"""
        business_data = {
            'name': '',
            'address': '',
            'phone': '',
            'website': '',
            'rating': '',
            'total_reviews': '',
            'category': '',
            'hours': '',
            'price_range': ''
        }
        
        try:
            # Wait for details panel to load
            time.sleep(3)
            
            # Business name - try multiple selectors (updated for current Google Maps)
            name_selectors = [
                "h1.DUwDvf.lfPIob",
                ".DUwDvf.lfPIob", 
                "h1",
                ".x3AX1-LfntMc-header-title-title",
                ".qrShPb .fontHeadlineLarge",
                "[data-attrid='title']",
                ".SPZz6b h1",
                ".qrShPb",
                "div[role='main'] h1"
            ]
            
            for selector in name_selectors:
                try:
                    name_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if name_elements:
                        name_text = name_elements[0].text.strip()
                        if name_text and name_text.lower() not in ['results', 'result', '', 'google maps']:
                            business_data['name'] = name_text
                            print(f"Found name with selector {selector}: {name_text}")
                            break
                except Exception as e:
                    continue
            
            # If still no name found, try a more general approach
            if not business_data['name']:
                try:
                    # Look for any heading or prominent text element
                    general_selectors = [
                        "h1, h2, h3",
                        "[data-value*='title'], [aria-label*='title']",
                        ".fontHeadlineLarge, .fontHeadlineMedium",
                        "[role='heading']"
                    ]
                    
                    for selector in general_selectors:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 3 and text.lower() not in ['results', 'result', 'google maps', 'directions', 'website']:
                                business_data['name'] = text
                                print(f"Found name with general selector {selector}: {text}")
                                break
                        if business_data['name']:
                            break
                except:
                    pass
            
            # Address - try multiple approaches
            address_selectors = [
                "[data-item-id='address']",
                ".rogA2c .Io6YTe",
                ".Io6YTe.fontBodyMedium", 
                "[data-value='Address']",
                ".AeaXub .fontBodyMedium",
                "button[data-item-id='address']",
                "[aria-label*='Address']"
            ]
            
            for selector in address_selectors:
                try:
                    address_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if address_elements:
                        address_text = address_elements[0].text.strip()
                        if address_text:
                            business_data['address'] = address_text
                            break
                except:
                    continue
            
            # Phone number
            phone_selectors = [
                "[data-item-id*='phone']",
                "[data-value='Phone']",
                ".rogA2c[data-item-id*='phone']",
                "button[data-item-id*='phone']",
                "[aria-label*='Phone'], [aria-label*='phone']"
            ]
            
            for selector in phone_selectors:
                try:
                    phone_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if phone_elements:
                        phone_text = phone_elements[0].text.strip()
                        if phone_text:
                            business_data['phone'] = phone_text
                            break
                except:
                    continue
            
            # Website
            try:
                website_selectors = [
                    "[data-item-id='authority']",
                    "a[href*='http']:not([href*='google']):not([href*='maps'])",
                    "button[data-item-id='authority']"
                ]
                
                for selector in website_selectors:
                    website_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if website_elements:
                        href = website_elements[0].get_attribute('href')
                        if href and 'google' not in href and 'maps' not in href:
                            business_data['website'] = href
                            break
            except:
                pass
            
            # Rating and reviews
            rating_selectors = [
                ".F7nice span",
                ".ceNzKf",
                "[data-value='Rating']",
                ".fontDisplayLarge",
                ".MW4etd",
                "span[aria-label*='stars']"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if rating_elements:
                        rating_text = rating_elements[0].text.strip()
                        if rating_text and any(char.isdigit() for char in rating_text):
                            # Extract rating and review count
                            if '(' in rating_text:
                                parts = rating_text.split('(')
                                business_data['rating'] = parts[0].strip()
                                if len(parts) > 1:
                                    business_data['total_reviews'] = parts[1].replace(')', '').strip()
                            else:
                                business_data['rating'] = rating_text
                            break
                except:
                    continue
            
            # Category
            category_selectors = [
                ".DkEaL",
                ".mgr77e .fontBodyMedium",
                "[data-value='Category']",
                ".AeaXub .fontBodyMedium",
                "button[jsaction*='category']"
            ]
            
            for selector in category_selectors:
                try:
                    category_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if category_elements:
                        category_text = category_elements[0].text.strip()
                        if category_text:
                            business_data['category'] = category_text
                            break
                except:
                    continue
                
        except Exception as e:
            print(f"Error extracting business data: {e}")
        
        # Debug: Print what we extracted
        if business_data['name']:
            print(f"Successfully extracted: {business_data['name']}")
        else:
            print("Failed to extract business name")
        
        return business_data if business_data['name'] and business_data['name'].lower() != 'results' else None
    
    def save_to_excel(self, results, filename=None):
        """Save results to Excel file"""
        if not results:
            return None
            
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"google_maps_results_{timestamp}.xlsx"
            
            # Ensure results directory exists
            os.makedirs("results", exist_ok=True)
            
            filepath = os.path.join("results", filename)
            df = pd.DataFrame(results)
            df.to_excel(filepath, index=False)
            return filepath
        except Exception as e:
            print(f"Error saving to Excel: {e}")
            return None
    
    def save_to_csv(self, results, filename=None):
        """Save results to CSV file"""
        if not results:
            return None
            
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"google_maps_results_{timestamp}.csv"
            
            # Ensure results directory exists
            os.makedirs("results", exist_ok=True)
            
            filepath = os.path.join("results", filename)
            df = pd.DataFrame(results)
            df.to_csv(filepath, index=False)
            return filepath
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return None