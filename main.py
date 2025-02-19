import argparse
import time
import logging
import os
from typing import Optional, Tuple, List, Dict, Any
from services.openai_service import OpenAIService
from services.sheets_service import SheetsService
from services.scraper_service import ScraperService
from services.serper_service import SerperService
from services.research_service import ResearchService

# Set up logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Only show httpx logs if DEBUG environment variable is set
if os.getenv("DEBUG"):
    logging.getLogger("httpx").setLevel(logging.INFO)
else:
    logging.getLogger("httpx").setLevel(logging.WARNING)

class TTRPGBlurbWriter:
    """Main class for managing TTRPG content generation and updates."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.sheets_service = SheetsService()
        self.serper_service = SerperService()
        self.research_service = ResearchService()

    def generate_game_content(
        self, 
        title: str, 
        column: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[List[Dict[str, Any]]], Optional[str], Optional[str]]:
        """
        Generate requested content for a game title.
        
        Args:
            title: Name of the game
            column: Specific column to update (if any)
            
        Returns:
            Tuple containing: summary, full_text, category, potential_categories, related_data, review_summary, reviews_url
        """
        summary = full_text = category = potential_categories = related_data = review_summary = reviews_url = None
        
        try:
            # Get notes for the game from the spreadsheet
            notes = self.sheets_service.get_notes(title)
            
            if not column or column == 'summary':
                logger.info("Getting TTRPG summary...")
                summary = self.openai_service.get_ttrpg_summary(title, notes)
            
            if not column or column == 'full_text':
                logger.info("Getting full text description...")
                research_prompt = f"""Create a detailed HTML article about the tabletop roleplaying game '{title}' that covers:
                - Theme and setting
                - Core mechanics and rules
                - What makes it unique
                - Target audience and player experience
                
                {"Additional context: " + notes if notes else ''}
                
                Format requirements:
                - Do not include any report intro or outro, start with the first section and end with the last section
                - Start headings with <h2> (no h1 tags)
                - Include specific examples and details
                - Keep the word count under 500 words"""
                
                # Strip any h1 tags from the beginning of the research output
                full_text = self.research_service.get_research(
                    game_title=title,
                    prompt=research_prompt
                )
                if full_text and full_text.strip().startswith("<h1>"):
                    full_text = full_text[full_text.find("</h1>") + 5:].strip()
            
            if not column or column == 'category':
                logger.info("Getting category...")
                category = self.openai_service.get_ttrpg_category(title)
            
            if not column or column == 'potential_categories':
                logger.info("Getting potential categories...")
                potential_categories = self.openai_service.get_potential_categories(title)
            
            if not column or column == 'related_games':
                logger.info("Getting related games...")
                if not category:
                    category = self.openai_service.get_ttrpg_category(title)
                
                worksheet = self.sheets_service.get_worksheet()
                related_games = self.openai_service.find_related_games_by_ai(worksheet, title)
                
                related_data = []
                for game in related_games:
                    blurb = self.openai_service.generate_relationship_blurb(
                        title, 
                        game['title'], 
                        game['categories']
                    )
                    related_data.append({
                        'title': game['title'],
                        'imgUrl': game['imgUrl'],
                        'page': game['page'],
                        'blurb': blurb
                    })
                
                # Ensure we have exactly 3 entries
                while len(related_data) < 3:
                    related_data.append({'title': '', 'imgUrl': '', 'page': '', 'blurb': ''})
            
            if not column or column in ['reviewSummary', 'reviewsUrl']:
                logger.info("Getting review summary...")
                review_summary, reviews_url = self.generate_review_summary(title)
            
            return summary, full_text, category, potential_categories, related_data, review_summary, reviews_url
            
        except Exception as e:
            logger.error(f"Error generating content for {title}: {str(e)}")
            raise

    def generate_review_summary(self, title: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate a summary of reviews for a game."""
        try:
            logger.info("Retrieving DriveThruRPG URL using Serper service...")
            
            # Use Serper service to get the URL
            url = self.serper_service.get_drivethrurpg_url(title)
            print("DRIVE THRU RPG URL", url)
            if not url:
                logger.warning(f"No DriveThruRPG URL found for {title}")
                return None, None
            
            # Get reviews from DriveThruRPG
            scraper = ScraperService()
            
            # Add delay before scraping to be respectful to the server
            time.sleep(2)
            
            rawHtml = scraper.scrape_drivethrurpg_html(url)
            if not rawHtml:
                logger.warning(f"No HTML content found for {title} at {url}")
                return None, None
            
            rawText = scraper.get_visible_text(rawHtml)
            if not rawText:
                logger.warning(f"No visible text found in HTML for {title} at {url}")
                return None, None
            
            reviews = self.openai_service.extract_reviews(rawText)
            if not reviews:
                logger.warning(f"No reviews found for {title} at {url}")
                return None, None
            
            logger.info(f"Found {len(reviews) if isinstance(reviews, list) else 'some'} reviews")
            
            # Generate summary using OpenAI
            summary = self.openai_service.summarize_reviews(reviews)
            logger.info("Generated review summary")
            return summary, url
            
        except Exception as e:
            logger.error(f"Error generating review summary for {title}: {str(e)}")
            return None, None

    def process_games(self, games: List[str], column: Optional[str] = None) -> None:
        """Process one or more games from the spreadsheet."""
        for i, title in enumerate(games, 1):
            logger.info(f"\nProcessing {i}/{len(games)}: {title}")
            try:
                content = self.generate_game_content(title, column)
                self.sheets_service.update_google_sheet(
                    game_name=title,
                    summary=content[0],
                    full_text=content[1],
                    category=content[2],
                    potential_categories=content[3],
                    related_data=content[4],
                    review_summary=content[5],
                    reviews_url=content[6],
                    specific_column=column
                )
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error processing {title}: {str(e)}")
                continue
        
        logger.info("\nBatch update completed!")

def main():
    """Main entry point for the TTRPG Blurb Writer."""
    parser = argparse.ArgumentParser(
        description='Generate and manage TTRPG game information in a Google Spreadsheet.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single game with all columns
  python main.py "Dungeons & Dragons"
  
  # Update only the summary for a game
  python main.py "Pathfinder" --column summary
  
  # Update related games for all entries
  python main.py --update-all -c related_games

    # Update all entries starting from row 10
  python main.py --update-all --start-row 10
  
Column Descriptions:
  summary              - A 2-3 sentence overview of the game
  full_text           - Detailed HTML-formatted description with multiple sections
  category            - 4-7 categories from predefined lists (genres, themes, mechanics)
  potential_categories - 2-3 suggested new categories not in the predefined lists
  related_games       - Find and describe 3 similar games from the database
  reviewSummary        - A summary of reviews for the game
  reviewsUrl           - URL to the reviews page
        """
    )
    
    parser.add_argument(
        'game_name', 
        nargs='*', 
        help='Name of the TTRPG game (if not using --update-all)'
    )
    parser.add_argument(
        '--column', 
        '-c',
        choices=['summary', 'full_text', 'category', 'potential_categories', 'related_games', 'reviewSummary', 'reviewsUrl'],
        help='Specific column to update (updates all columns if not specified)'
    )
    parser.add_argument(
        '--update-all',
        action='store_true',
        help='Update all games in the spreadsheet instead of a single game'
    )
    parser.add_argument(
        '--start-row',
        type=int,
        default=2,
        help='Row number to start updating from when using --update-all (default: 2)'
    )
    
    args = parser.parse_args()

    try:
        writer = TTRPGBlurbWriter()
        
        if args.update_all:
            worksheet = writer.sheets_service.get_worksheet()
            titles = [t for t in worksheet.col_values(1)[args.start_row-1:] if t.strip()]
            writer.process_games(titles, args.column)
        else:
            ttrpg_name = ' '.join(args.game_name) if args.game_name else input("Enter the name of the TTRPG: ").strip()
            if not ttrpg_name:
                logger.error("Please provide a valid name.")
                return

            writer.process_games([ttrpg_name], args.column)
            logger.info("Successfully uploaded the data to Google Sheet!")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
