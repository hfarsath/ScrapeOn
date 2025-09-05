# scrapers/phone_scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import pandas as pd
import time
import re
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import os

class PhoneScraper:
    def __init__(self):
        self.driver = None
        self.results = []
        self.phones_found = set()
        
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
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return False
    
    def scrape(self, query, pages=3, progress_callback=None, stop_callback=None):
        """Scrape phone numbers from Google search results"""
        self.results = []
        self.phones_found = set()
        
        if not self.setup_driver():
            if progress_callback:
                progress_callback("❌ Error: Could not setup Chrome driver")
            return []
        
        try:
            if progress_callback:
                progress_callback(f"🔍 Searching for: {query}")
            
            # Search on Google
            search_url = f"https://www.google.com/search?q={quote(query)}"
            self.driver.get(search_url)
            time.sleep(3)
            
            # Extract URLs from multiple pages
            all_urls = []
            for page in range(pages):
                # Check for stop signal
                if stop_callback and stop_callback():
                    if progress_callback:
                        progress_callback("Phone scraping stopped by user")
                    break
                    
                if progress_callback:
                    progress_callback(f"📄 Scraping page {page + 1} of {pages}")
                
                urls = self.extract_urls_from_page()
                all_urls.extend(urls)
                
                # Go to next page
                if page < pages - 1:
                    try:
                        next_button = self.driver.find_element(By.ID, "pnnext")
                        next_button.click()
                        time.sleep(3)
                    except:
                        if progress_callback:
                            progress_callback(f"⚠️ No more pages available (stopped at page {page + 1})")
                        break
            
            if progress_callback:
                progress_callback(f"📎 Found {len(all_urls)} URLs to scan for phone numbers")
            
            # Extract phone numbers from each URL
            for i, url in enumerate(all_urls):
                # Check for stop signal
                if stop_callback and stop_callback():
                    if progress_callback:
                        progress_callback("Phone scraping stopped by user")
                    break
                    
                if progress_callback:
                    progress_callback(f"🔍 Scanning URL {i + 1}/{len(all_urls)}: {url[:50]}...")
                
                phones = self.extract_phones_from_url(url)
                if phones:
                    for phone in phones:
                        if phone not in self.phones_found:
                            self.phones_found.add(phone)
                            self.results.append({
                                'phone': phone,
                                'formatted_phone': self.format_phone(phone),
                                'source_url': url,
                                'found_at': time.strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            if progress_callback:
                                progress_callback(f"📞 Found phone: {phone}")
                
                # Small delay to avoid being blocked
                time.sleep(1)
            
            if not stop_callback or not stop_callback():
                if progress_callback:
                    progress_callback(f"✅ Phone scraping completed! Found {len(self.results)} unique phone numbers")
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Error during scraping: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                
        return self.results
    
    def extract_urls_from_page(self):
        """Extract URLs from current Google search results page"""
        urls = []
        try:
            # Find search result links
            result_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='http']")
            
            for link in result_links:
                try:
                    href = link.get_attribute('href')
                    if href and self.is_valid_url(href):
                        urls.append(href)
                except:
                    continue
                    
        except Exception as e:
            print(f"Error extracting URLs: {e}")
            
        return list(set(urls))  # Remove duplicates
    
    def is_valid_url(self, url):
        """Check if URL is valid for phone extraction"""
        if not url or not url.startswith('http'):
            return False
            
        # Skip Google's own URLs and some social media
        skip_domains = [
            'google.com', 'youtube.com', 'facebook.com', 'twitter.com',
            'linkedin.com', 'instagram.com', 'pinterest.com'
        ]
        
        for domain in skip_domains:
            if domain in url:
                return False
                
        return True
    
    def extract_phones_from_url(self, url):
        """Extract phone numbers from a specific URL"""
        phones = []
        
        try:
            # First try with Selenium
            self.driver.get(url)
            time.sleep(3)
            page_source = self.driver.page_source
            
            # Extract phone numbers using multiple regex patterns
            phone_patterns = [
                # US formats with country code
                r'\+1[\s\-\.]?\(?([0-9]{3})\)?[\s\-\.]?([0-9]{3})[\s\-\.]?([0-9]{4})\b',
                # US formats without country code
                r'\(?([0-9]{3})\)?[\s\-\.]?([0-9]{3})[\s\-\.]?([0-9]{4})\b',
                # International formats
                r'\+[1-9]\d{1,14}\b',
                # General patterns
                r'\b\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{4}\b',
                # Pattern with parentheses
                r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',
                # Indian mobile numbers
                r'\+91[\s\-]?\d{10}',
                r'\b[6-9]\d{9}\b'
            ]
            
            found_phones = set()
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    if isinstance(match, tuple):
                        # Join tuple elements for US format
                        phone_str = ''.join(match)
                    else:
                        phone_str = match
                    
                    # Clean and validate
                    cleaned_phone = self.clean_phone(phone_str)
                    if self.is_valid_phone(cleaned_phone):
                        found_phones.add(cleaned_phone)
            
            phones.extend(list(found_phones))
                        
        except Exception as e:
            # If Selenium fails, try with requests
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    # Use the same patterns as above
                    phone_patterns = [
                        r'\+1[\s\-\.]?\(?([0-9]{3})\)?[\s\-\.]?([0-9]{3})[\s\-\.]?([0-9]{4})\b',
                        r'\(?([0-9]{3})\)?[\s\-\.]?([0-9]{3})[\s\-\.]?([0-9]{4})\b',
                        r'\+[1-9]\d{1,14}\b',
                        r'\b\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{4}\b'
                    ]
                    
                    found_phones = set()
                    for pattern in phone_patterns:
                        matches = re.findall(pattern, response.text)
                        for match in matches:
                            phone_str = ''.join(match) if isinstance(match, tuple) else match
                            cleaned_phone = self.clean_phone(phone_str)
                            if self.is_valid_phone(cleaned_phone):
                                found_phones.add(cleaned_phone)
                    
                    phones.extend(list(found_phones))
            except Exception as req_error:
                pass
        
        return list(set(phones))  # Remove duplicates
    
    def clean_phone(self, phone):
        """Clean phone number string"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', str(phone))
        
        # Handle US numbers
        if cleaned.startswith('1') and len(cleaned) == 11:
            cleaned = cleaned[1:]  # Remove leading 1
        elif cleaned.startswith('+1') and len(cleaned) == 12:
            cleaned = cleaned[2:]  # Remove +1
        
        return cleaned
    
    def is_valid_phone(self, phone):
        """Validate phone number"""
        if not phone:
            return False
        
        # Remove any remaining non-digits
        digits_only = re.sub(r'\D', '', phone)
        
        # Check length (allow 10-15 digits for international numbers)
        if len(digits_only) < 10 or len(digits_only) > 15:
            return False
        
        # For 10-digit numbers (US format)
        if len(digits_only) == 10:
            # First digit should not be 0 or 1
            if digits_only[0] in ['0', '1']:
                return False
        
        # For 11-digit numbers (US with country code)
        if len(digits_only) == 11:
            # Should start with 1 for US
            if not digits_only.startswith('1'):
                return False
            # Area code (2nd-4th digits) should not start with 0 or 1
            if digits_only[1] in ['0', '1']:
                return False
        
        # Check for obviously invalid patterns
        invalid_patterns = [
            '0000000000', '1111111111', '2222222222', '3333333333',
            '4444444444', '5555555555', '6666666666', '7777777777',
            '8888888888', '9999999999', '1234567890', '0123456789',
            '9876543210'
        ]
        
        # Check against 10-digit version for invalid patterns
        check_digits = digits_only[-10:] if len(digits_only) > 10 else digits_only
        if check_digits in invalid_patterns:
            return False
        
        return True
    
    def format_phone(self, phone):
        """Format phone number for display"""
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone
    
    def save_to_excel(self, results, filename=None):
        """Save results to Excel file"""
        if not results:
            return None
            
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"phone_scraper_results_{timestamp}.xlsx"
            
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
                filename = f"phone_scraper_results_{timestamp}.csv"
            
            os.makedirs("results", exist_ok=True)
            filepath = os.path.join("results", filename)
            df = pd.DataFrame(results)
            df.to_csv(filepath, index=False)
            return filepath
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return None