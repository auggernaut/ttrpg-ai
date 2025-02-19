import os
import logging
import requests
from typing import Optional
from utils.decorators import retry_with_backoff

logger = logging.getLogger(__name__)

class ResearchService:
    """Service to interact with the Deep Research API."""
    
    def __init__(self):
        self.api_key = os.getenv("RESEARCH_API_KEY")
        # Default to http://localhost:3000 for development
        self.base_url = os.getenv("RESEARCH_API_URL", "http://localhost:3000/api/research")
        
    @retry_with_backoff
    def get_research(
        self, 
        game_title: str, 
        prompt: str, 
        model: str = "google__gemini-flash"
    ) -> Optional[str]:
        """
        Get research analysis for a given game title and prompt.
        
        Args:
            game_title: The name of the game to research
            prompt: Specific research prompt/question
            model: The AI model to use (defaults to gpt-4o)
            
        Returns:
            HTML formatted research report or None if the request fails
        """
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}' if self.api_key else None
            }
            
            # Remove None values from headers
            headers = {k: v for k, v in headers.items() if v is not None}
            
            payload = {
                'query': game_title + ' ttrpg',
                'prompt': prompt,
                'model': model
            }
            
            # For development, disable SSL verification if using localhost
            verify_ssl = not self.base_url.startswith('http://localhost')
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                verify=verify_ssl
            )
            response.raise_for_status()
            
            return response.text
            
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error connecting to research service: {str(e)}")
            # Fallback to OpenAI service
            from services.openai_service import OpenAIService
            openai = OpenAIService()
            return openai.get_ttrpg_full_text(game_title, prompt)
            
        except Exception as e:
            logger.error(f"Error getting research for {game_title}: {str(e)}")
            # Fallback to OpenAI service
            from services.openai_service import OpenAIService
            openai = OpenAIService()
            return openai.get_ttrpg_full_text(game_title, prompt) 