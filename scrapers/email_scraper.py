# scrapers/email_scraper.py
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

class EmailScraper:
    def __init__(self):
        self.driver = None
        self.results = []
        self.emails_found = set()
        
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
        """Scrape emails from Google search results"""
        self.results = []
        self.emails_found = set()
        
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
                        progress_callback("Email scraping stopped by user")
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
                progress_callback(f"📎 Found {len(all_urls)} URLs to scan for emails")
            
            # Extract emails from each URL
            for i, url in enumerate(all_urls):
                # Check for stop signal
                if stop_callback and stop_callback():
                    if progress_callback:
                        progress_callback("Email scraping stopped by user")
                    break
                    
                if progress_callback:
                    progress_callback(f"🔍 Scanning URL {i + 1}/{len(all_urls)}: {url[:50]}...")
                
                emails = self.extract_emails_from_url(url)
                if emails:
                    for email in emails:
                        if email not in self.emails_found:
                            self.emails_found.add(email)
                            self.results.append({
                                'email': email,
                                'source_url': url,
                                'domain': email.split('@')[1] if '@' in email else '',
                                'found_at': time.strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            if progress_callback:
                                progress_callback(f"✉️ Found email: {email}")
                
                # Small delay to avoid being blocked
                time.sleep(1)
            
            if not stop_callback or not stop_callback():
                if progress_callback:
                    progress_callback(f"✅ Email scraping completed! Found {len(self.results)} unique emails")
                
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
        """Check if URL is valid for email extraction"""
        if not url or not url.startswith('http'):
            return False
            
        # Skip Google's own URLs and ads
        skip_domains = [
            'google.com', 'youtube.com', 'facebook.com', 'twitter.com',
            'linkedin.com', 'instagram.com', 'pinterest.com'
        ]
        
        for domain in skip_domains:
            if domain in url:
                return False
                
        return True
    
    def extract_emails_from_url(self, url):
        """Extract emails from a specific URL"""
        emails = []
        
        try:
            # First try with Selenium
            self.driver.get(url)
            time.sleep(3)  # Increased wait time
            page_source = self.driver.page_source
            
            # Extract emails using regex
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            found_emails = email_pattern.findall(page_source)
            
            # Filter out common false positives
            for email in found_emails:
                if self.is_valid_email(email):
                    emails.append(email.lower())
                    
        except Exception as e:
            # If Selenium fails, try with requests
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
                    found_emails = email_pattern.findall(response.text)
                    
                    for email in found_emails:
                        if self.is_valid_email(email):
                            emails.append(email.lower())
            except:
                pass
        
        return list(set(emails))  # Remove duplicates
    
    def is_valid_email(self, email):
        """Validate email address"""
        if not email or '@' not in email:
            return False
            
        # Skip common false positives
        false_positives = [
            'example@', '@example', 'test@', '@test', 'admin@admin',
            'user@user', 'email@email', 'contact@contact', 'noreply@',
            'no-reply@', 'donotreply@', 'info@info', 'support@support'
        ]
        
        email_lower = email.lower()
        for fp in false_positives:
            if fp in email_lower:
                return False
        
        # Basic email validation
        parts = email.split('@')
        if len(parts) != 2:
            return False
            
        local, domain = parts
        if len(local) < 1 or len(domain) < 3:
            return False
            
        if '.' not in domain:
            return False
            
        # Check for valid domain extensions
        domain_parts = domain.split('.')
        if len(domain_parts[-1]) < 2:
            return False
            
        return True
    
    def save_to_excel(self, results, filename=None):
        """Save results to Excel file"""
        if not results:
            return None
            
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"email_scraper_results_{timestamp}.xlsx"
            
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
                filename = f"email_scraper_results_{timestamp}.csv"
            
            os.makedirs("results", exist_ok=True)
            filepath = os.path.join("results", filename)
            df = pd.DataFrame(results)
            df.to_csv(filepath, index=False)
            return filepath
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return None