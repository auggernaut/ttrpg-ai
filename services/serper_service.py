import requests
import logging
from typing import Optional
import os

class SerperService:
    """Service to interact with Serper API for retrieving URLs."""
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")  # Ensure you have this in your .env file
        self.base_url = "https://google.serper.dev/search"
        self.logger = logging.getLogger(__name__)

    def search(self, query):
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = {'q': query}
        response = requests.post(self.base_url, headers=headers, json=payload)
        return response.json() 

    def get_drivethrurpg_url(self, title: str) -> Optional[str]:
        """Fetch the DriveThruRPG URL for a given game title."""
        try:
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                'q': f"{title} site:drivethrurpg.com"
            }
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            print("serper data", data)
            # Assuming the first result is the most relevant
            if data and "organic" in data and len(data["organic"]) > 0:
                return data["organic"][0]["link"]
            
            self.logger.warning(f"No results found for {title}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching URL for {title}: {str(e)}")
            return None 