import gspread
import logging
from typing import List, Dict, Optional, Any, Tuple
from config.constants import SERVICE_ACCOUNT_FILE
from utils.decorators import retry_with_backoff

# Set up logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class SheetsService:
    """Service class for handling Google Sheets operations."""
    
    # Column mappings for the spreadsheet
    COLUMN_MAPPING = {
        'summary': 6,      # text column
        'full_text': 7,    # fullText column
        'category': 9,     # Category column
        'potential_categories': 10,    # Potential Categories column
        'reviewSummary': 5,  # Column E
        'related_games': [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
    }

    @staticmethod
    def get_worksheet():
        """Get the main worksheet from the TTRPG Directory spreadsheet."""
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        return gc.open("TTRPG Directory").sheet1

    @staticmethod
    def _format_page_name(game_name: str) -> str:
        """Format game name for page URL."""
        return ''.join(e.lower() for e in game_name if e.isalnum())

    @classmethod
    def _update_related_games(cls, worksheet, row_index: int, related_data: List[Dict], columns: List[int]):
        """Update related games data in the worksheet."""
        for i, col in enumerate(columns):
            game_index = i // 4
            field_index = i % 4
            value = ''
            if game_index < len(related_data):
                if field_index == 0: value = related_data[game_index]['title']
                elif field_index == 1: value = related_data[game_index]['imgUrl']
                elif field_index == 2: value = related_data[game_index]['page']
                elif field_index == 3: value = related_data[game_index]['blurb']
            worksheet.update_cell(row_index, col, value)

    @classmethod
    @retry_with_backoff
    def update_google_sheet(
        cls,
        game_name: str,
        summary: Optional[str] = None,
        full_text: Optional[str] = None,
        category: Optional[str] = None,
        potential_categories: Optional[str] = None,
        review_summary: Optional[str] = None,
        related_data: Optional[List[Dict]] = None,
        specific_column: Optional[str] = None
    ) -> bool:
        """
        Update or create an entry in the Google Sheet.
        
        Args:
            game_name: Name of the game
            summary: Game summary
            full_text: Detailed game description
            category: Game categories
            potential_categories: Suggested new categories
            review_summary: Review summary
            related_data: Related games information
            specific_column: Specific column to update (if any)
        
        Returns:
            bool: Success status
        """
        try:
            worksheet = cls.get_worksheet()
            titles = worksheet.col_values(1)  # Column A contains titles
            
            # Find existing row
            row_index = next(
                (i for i, title in enumerate(titles, start=1) 
                 if title.lower() == game_name.lower()),
                None
            )
            
            if row_index:
                logger.info(f"Updating existing entry for {game_name}...")
                if specific_column:
                    if specific_column not in cls.COLUMN_MAPPING:
                        raise ValueError(f"Invalid column name: {specific_column}")
                    
                    if specific_column == 'related_games' and related_data:
                        cls._update_related_games(
                            worksheet, 
                            row_index, 
                            related_data, 
                            cls.COLUMN_MAPPING['related_games']
                        )
                    else:
                        value = review_summary if specific_column == 'reviewSummary' else locals()[specific_column]
                        if value:
                            worksheet.update_cell(
                                row_index, 
                                cls.COLUMN_MAPPING[specific_column], 
                                value
                            )
                else:
                    # Update all provided columns
                    for col_name, col_var in [
                        ('summary', summary),
                        ('full_text', full_text),
                        ('category', category),
                        ('potential_categories', potential_categories)
                    ]:
                        if col_var:
                            worksheet.update_cell(
                                row_index, 
                                cls.COLUMN_MAPPING[col_name], 
                                col_var
                            )
                    if related_data:
                        cls._update_related_games(
                            worksheet, 
                            row_index, 
                            related_data, 
                            cls.COLUMN_MAPPING['related_games']
                        )
            else:
                logger.info(f"Adding new entry for {game_name}...")
                page_name = cls._format_page_name(game_name)
                new_row = [
                    game_name,  # title
                    '',        # url
                    '',        # imgUrl
                    page_name, # page
                    '',        # reviewSummary
                    summary,   # text
                    full_text, # fullText
                    '',        # notes
                    category,  # Category
                    potential_categories,  # Potential Categories
                    '',  # Rank
                    True,  # Hidden
                    False,  # isFree
                    False,  # isTopRated
                    True,  # verified
                    False  # premium
                ]
                
                # Pad the row to match all columns
                while len(new_row) < len(worksheet.row_values(1)):
                    new_row.append('')
                
                worksheet.append_row(new_row)
                row_index = len(worksheet.col_values(1))
                
                if related_data:
                    cls._update_related_games(
                        worksheet, 
                        row_index, 
                        related_data, 
                        cls.COLUMN_MAPPING['related_games']
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating spreadsheet: {e}")
            return False

    @classmethod
    def get_all_games(cls) -> List[Dict[str, Any]]:
        """Get all games from the worksheet."""
        worksheet = cls.get_worksheet()
        return worksheet.get_all_records()

    def get_notes(self, game_name: str) -> Optional[str]:
        """Get notes for a specific game from the spreadsheet."""
        worksheet = self.get_worksheet()
        
        # Find the row for the game
        try:
            cell = worksheet.find(game_name)
            if cell:
                # Assuming notes are in a specific column, e.g., column J (10)
                notes_col = 10  # Adjust this to match your actual notes column
                notes = worksheet.cell(cell.row, notes_col).value
                return notes if notes else None
        except Exception as e:
            logger.debug(f"Could not find notes for {game_name}: {str(e)}")
            return None

    def get_url(self, title: str) -> Optional[str]:
        """Get the URL for a given game title."""
        worksheet = self.get_worksheet()
        # Find the row with the matching title
        try:
            cell = worksheet.find(title)
            if cell:
                # Get the URL from column B in the same row
                return worksheet.cell(cell.row, 2).value
        except:
            return None
        return None
