from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict
import time

class ScraperService:
    def __init__(self):
        self.driver = None

    def initialize_driver(self):
        """Initialize the Chrome WebDriver."""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--disk-cache-size=50000000')
        chrome_options.add_argument('--media-cache-size=50000000')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--silent')
        self.driver = webdriver.Chrome(options=chrome_options)
        

    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()

    def scrape_drivethrurpg_html(self, url: str) -> str:
        """
        Scrape reviews from a DriveThruRPG product page.
        
        Args:
            url: Direct URL to the DriveThruRPG product page
                (e.g., 'https://www.drivethrurpg.com/product/...')
            
        Returns:
            String containing the page HTML
        
        Raises:
            ValueError: If the URL is not a valid DriveThruRPG product URL
        """
        if not url.startswith('https://www.drivethrurpg.com/'):
            print(url)
            raise ValueError('URL must be a DriveThruRPG product page URL')
        
        try:
            self.initialize_driver()
            
            # Navigate directly to the product page
            self.driver.get(url)
            
            # Wait for the main content to load
            time.sleep(5)
            
            try:
                # Try to find the "View more discussions" button with a shorter timeout
                more_reviews_button = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'View more discussions')]"))
                )
                
                # If button exists, try to click it
                if more_reviews_button:
                    # Scroll to button with offset to ensure it's in view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_reviews_button)
                    time.sleep(1)
                    
                    try:
                        more_reviews_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", more_reviews_button)
                        
                    print("Clicked 'View more discussions' button")
                    time.sleep(2)
                    
            except TimeoutException:
                # This is expected for pages with few reviews
                print("No 'View more discussions' button found (this is normal for pages with few reviews)")
            except Exception as e:
                print(f"Non-critical error handling reviews button: {type(e).__name__} - {str(e)}")
            
            return self.driver.page_source
        finally:
            self.close_driver()

    def get_visible_text(self, html_content):
        """Extract visible text from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        text = soup.get_text(separator=' ')
        return text






