import argparse
import time
import logging
import os
from typing import Optional, Tuple, List, Dict, Any
from services.openai_service import OpenAIService
from services.sheets_service import SheetsService

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

    def generate_game_content(
        self, 
        title: str, 
        column: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Generate requested content for a game title.
        
        Args:
            title: Name of the game
            column: Specific column to update (if any)
            
        Returns:
            Tuple containing: summary, full_text, category, potential_categories, related_data
        """
        summary = full_text = category = potential_categories = related_data = None
        
        try:
            # Get notes for the game from the spreadsheet
            notes = self.sheets_service.get_notes(title)
            
            if not column or column == 'summary':
                logger.info("Getting TTRPG summary...")
                summary = self.openai_service.get_ttrpg_summary(title, notes)
            
            if not column or column == 'full_text':
                logger.info("Getting full text description...")
                full_text = self.openai_service.get_ttrpg_full_text(title, notes)
            
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
            
            return summary, full_text, category, potential_categories, related_data
            
        except Exception as e:
            logger.error(f"Error generating content for {title}: {str(e)}")
            raise

    def process_all_games(self, column: Optional[str] = None) -> None:
        """Process all games in the spreadsheet."""
        worksheet = self.sheets_service.get_worksheet()
        titles = [t for t in worksheet.col_values(1)[1:] if t.strip()]
        
        for i, title in enumerate(titles, 1):
            logger.info(f"\nProcessing {i}/{len(titles)}: {title}")
            try:
                content = self.generate_game_content(title, column)
                self.sheets_service.update_google_sheet(
                    game_name=title,
                    summary=content[0],
                    full_text=content[1],
                    category=content[2],
                    potential_categories=content[3],
                    related_data=content[4],
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
  python main.py "Pathfinder" -c summary
  
  # Update related games for all entries
  python main.py --update-all -c related_games
  
Column Descriptions:
  summary              - A 2-3 sentence overview of the game
  full_text           - Detailed HTML-formatted description with multiple sections
  category            - 4-7 categories from predefined lists (genres, themes, mechanics)
  potential_categories - 2-3 suggested new categories not in the predefined lists
  related_games       - Find and describe 3 similar games from the database
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
        choices=['summary', 'full_text', 'category', 'potential_categories', 'related_games'],
        help='Specific column to update (updates all columns if not specified)'
    )
    parser.add_argument(
        '--update-all',
        action='store_true',
        help='Update all games in the spreadsheet instead of a single game'
    )
    
    args = parser.parse_args()
    writer = TTRPGBlurbWriter()

    try:
        if args.update_all:
            writer.process_all_games(args.column)
        else:
            # Single game processing
            ttrpg_name = ' '.join(args.game_name) if args.game_name else input("Enter the name of the TTRPG: ").strip()
            if not ttrpg_name:
                logger.error("Please provide a valid name.")
                return

            logger.info(f"Processing: {ttrpg_name}")
            content = writer.generate_game_content(ttrpg_name, args.column)
            writer.sheets_service.update_google_sheet(
                game_name=ttrpg_name,
                summary=content[0],
                full_text=content[1],
                category=content[2],
                potential_categories=content[3],
                related_data=content[4],
                specific_column=args.column
            )
            logger.info("Successfully uploaded the data to Google Sheet!")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
