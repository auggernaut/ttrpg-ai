from openai import OpenAI
import gspread
from dotenv import load_dotenv
import os
from googlesearch import search
import sys
import argparse
import time
from gspread.exceptions import APIError

# Load environment variables
load_dotenv()

# Initialize constants
GPT_MODEL = "gpt-4o-mini"

# Initialize the client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Predefined categories list, organized by type
GENRES = [
    "Fantasy",
    "High-Fantasy",
    "Dark Fantasy",
    "Science Fiction",
    "Cyberpunk",
    "Post-Apocalyptic",
    "Horror",
    "Cosmic Horror",
    "Urban Fantasy",
    "Space Opera",
    "Sword-and-Sorcery",
    "Gothic",
    "Supernatural",
    "Military",
    "Mystery",
    "Historical",
    "Modern",
    "Dystopian",
    "Space-Western",
    "Nordic Mythology",
    "Aliens",
    "Interstellar Travel",
    "Star Trek",
    "Star Wars",
    "Mythological",
    "Comedy",
    "Superhero",
    "Heist",    
]

THEMES = [
    "Dark",
    "Mature",
    "Political",
    "Social Intrigue",
    "Psychological",
    "Environmental",
    "Bleak",
    "Metal",
    "Feminist",
    "Cinematic",
    "Romantic"
]

MECHANICS = [
    "Old-School Renaissance (OSR)",
    "Forged in the Dark (FitD)",
    "Powered by the Apocalypse (PbtA)",
    "New School Revolution (NSR)",
    "Class-based",
    "Classless",
    "Universal",
    "Narrative-Driven",
    "Tactical",
    "Real-Time Mechanics",
    "Streamlined",
    "Resource Management",
    "Character Customization",
    "Exploration-Driven",
    "Survival",
    "Investigation",
    "Team-Based",
    "Solo Play",
    "Tactical Combat",
    "Skill-based",
    "Low Magic",
    "Sandbox",
    "Collaborative Worldbuilding",
    "Quick-Play",
    "Rules Lite"
]

# Combine all categories
CATEGORIES = GENRES + THEMES + MECHANICS

def retry_with_backoff(func):
    def wrapper(*args, **kwargs):
        max_retries = 5
        retry_count = 0
        base_delay = 1  # Start with 1 second delay

        while retry_count < max_retries:
            try:
                return func(*args, **kwargs)
            except APIError as e:
                if "429" in str(e):  # Rate limit error
                    retry_count += 1
                    if retry_count == max_retries:
                        raise Exception(f"Max retries ({max_retries}) exceeded: {str(e)}")
                    
                    delay = base_delay * (2 ** retry_count)  # Exponential backoff
                    print(f"Rate limit hit. Waiting {delay} seconds before retry {retry_count}/{max_retries}...")
                    time.sleep(delay)
                else:
                    raise e
    return wrapper

@retry_with_backoff
def get_ttrpg_summary(game_name):
    prompt = f"""Write a short, engaging blurb about the tabletop roleplaying game '{game_name}'. 
Include its theme, key features, and what makes it unique. Keep it between 2-3 sentences. It should read more like an explanation of the game and not an advertisement.

Here are some examples of the style I'm looking for:

For "Blades in the Dark":
Blades in the Dark offers a gripping foray into a Victorian-inspired, ghost-infested city where players lead a crew of criminals undertaking high-stakes heists. The game stands out with its narrative-driven, team-based mechanics and a unique cycle of action and consequence that challenges players to think strategically and cooperate effectively.

For "Dungeon World":
Dungeon World is a streamlined tabletop RPG that focuses on storytelling and character development within a classic fantasy setting. It uses simple mechanics derived from the Powered by the Apocalypse system, facilitating fast-paced, collaborative storytelling. The game emphasizes player choices and narrative consequences, making it an excellent choice for those who value creative freedom and dynamic, character-driven adventures.

Please write a similar style blurb for: {game_name}"""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

@retry_with_backoff
def get_ttrpg_full_text(game_name):
    prompt = f"""Write a detailed description of the tabletop roleplaying game '{game_name}' formatted in HTML using <article> and <section> blocks. Include its theme, rules overview, unique mechanics, and target audience. 

Important: Do not use <h1> tags. Start your sections with <h2> if headings are needed. The output should start and end with <article> tags.

The description should cover:
- Theme and setting
- Core mechanics
- What makes it unique
- Target audience and complexity level"""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

@retry_with_backoff
def get_ttrpg_category(game_name):
    genres_string = '; '.join(GENRES)
    themes_string = '; '.join(THEMES)
    mechanics_string = '; '.join(MECHANICS)
    
    prompt = f"""Analyze the tabletop roleplaying game '{game_name}' and select 4-7 categories total from the following lists. Choose categories that best capture the game's core essence and unique features. Provide the categories separated by a semicolon and space.

Requirements:
- Must include at least one GENRE
- Must include at least one THEME
- Must include at least one MECHANIC/SYSTEM
- Total categories should be between 4 and 7
- List most important categories first

GENRES: {genres_string}

THEMES: {themes_string}

MECHANICS & SYSTEMS: {mechanics_string}

Example responses:
- For D&D 5E: Fantasy; High-Fantasy; Class-based; Character Customization; Tactical Combat; Team-Based
- For Blades in the Dark: Dark Fantasy; Gothic; Dark; Heist; Narrative-Driven; Team-Based
- For Mothership: Science Fiction; Horror; Psychological; Survival; Resource Management;

Important: Select only the categories that truly define the game's core identity, ordered by importance."""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

@retry_with_backoff
def get_potential_categories(game_name):
    prompt = f"""Analyze the tabletop roleplaying game '{game_name}' and suggest 2-3 new potential categories or tags that aren't in the following list. 
These should be unique, specific categories that could be useful for categorizing this and similar games. Format your response as a semicolon-separated list.

Existing categories: {'; '.join(CATEGORIES)}"""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

@retry_with_backoff
def find_related_games_by_category(worksheet, current_game, current_categories):
    try:
        # Get all data
        all_data = worksheet.get_all_records()
        
        # Convert current categories to a set for comparison
        current_cats = set(current_categories.lower().split('; '))
        
        # Score each game based on category matches
        scored_games = []
        for row in all_data:
            if row['title'].lower() == current_game.lower():
                continue  # Skip current game
                
            if not row['Category']:  # Skip entries without categories
                continue
                
            other_cats = set(row['Category'].lower().split('; '))
            matches = len(current_cats.intersection(other_cats))
            
            if matches > 0:  # Only include games with at least one matching category
                scored_games.append({
                    'title': row['title'],
                    'imgUrl': row['imgUrl'],
                    'page': row['page'],
                    'categories': row['Category'],
                    'score': matches
                })
        
        # Sort by score and return top 3
        return sorted(scored_games, key=lambda x: x['score'], reverse=True)[:3]
    except Exception as e:
        print(f"Error finding related games: {e}")
        return []

@retry_with_backoff
def find_related_games_by_ai(worksheet, current_game):
    try:
        # Get all game titles
        all_data = worksheet.get_all_records()
        game_titles = [row['title'] for row in all_data if row['title'].lower() != current_game.lower()]
        
        # Create prompt for AI
        titles_list = ', '.join(game_titles[:100])  # Limit to first 100 games to stay within token limits
        prompt = f"""Given the tabletop RPG "{current_game}" and the following list of other TTRPGs, identify the 3 most similar or related games. Consider mechanics, themes, and target audience. Only select from the provided list:

{titles_list}

Format your response as a semicolon-separated list of exactly 3 games. Example: "Game1; Game2; Game3"
Important: Only include games from the provided list. You must return exactly3 games."""

        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        
        related_titles = response.choices[0].message.content.strip().split('; ')
        
        # Find the full data for the related games
        related_games = []
        for title in related_titles:
            game_data = next((row for row in all_data if row['title'].lower() == title.lower()), None)
            if game_data:
                related_games.append({
                    'title': game_data['title'],
                    'imgUrl': game_data['imgUrl'],
                    'page': game_data['page'],
                    'categories': game_data.get('Category', '')
                })
        
        return related_games
    except Exception as e:
        print(f"Error finding related games by AI: {e}")
        return []

def generate_relationship_blurb(game1_name, game2_name, game2_categories):
    prompt = f"""Write a brief 1-2 sentence description of how the tabletop RPG "{game2_name}" relates to "{game1_name}". 
Focus on their shared elements or complementary features, especially how they differ in play style and game mechanics. Also an example of how they differ.
Wrap any titles in <i> tags.
Categories for {game2_name}: {game2_categories}"""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def update_related_games(worksheet, row_index, related_data, columns):
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

def get_worksheet():
    """Get the main worksheet from the TTRPG Directory spreadsheet."""
    gc = gspread.service_account(filename='ttrpg-games-9a5bfcb02194.json')
    return gc.open("TTRPG Directory").sheet1

@retry_with_backoff
def update_google_sheet(sheet_name, game_name, summary, full_text, category, potential_categories, related_data=None, specific_column=None):
    worksheet = get_worksheet()
    
    # Define column mappings
    column_mapping = {
        'summary': 6,      # text column
        'full_text': 7,    # fullText column
        'category': 9,     # Category column
        'potential_categories': 10,    # Potential Categories column
        'related_games': [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]  # Updated to include 4 more columns
    }
    
    # Format page name: lowercase, no spaces or special characters
    page_name = ''.join(e.lower() for e in game_name if e.isalnum())
    
    try:
        # Find all titles
        titles = worksheet.col_values(1)  # Column A contains titles
        
        # Look for matching title (case insensitive)
        row_index = None
        for i, title in enumerate(titles, start=1):
            if title.lower() == game_name.lower():
                row_index = i
                break
        
        if row_index:
            print(f"Updating existing entry for {game_name}...")
            # Check if updating specific column or all columns
            if specific_column:
                if specific_column not in column_mapping:
                    raise ValueError(f"Invalid column name: {specific_column}")
                # Update only the specified column
                if specific_column == 'related_games' and related_data:
                    update_related_games(worksheet, row_index, related_data, column_mapping['related_games'])
                else:
                    value = locals()[specific_column]  # Get value using column name
                    if value:
                        worksheet.update_cell(row_index, column_mapping[specific_column], value)
            else:
                # Update all columns that have data
                for col_name, col_var in [
                    ('summary', summary),
                    ('full_text', full_text),
                    ('category', category),
                    ('potential_categories', potential_categories)
                ]:
                    if col_var:
                        worksheet.update_cell(row_index, column_mapping[col_name], col_var)
                if related_data:
                    update_related_games(worksheet, row_index, related_data, column_mapping['related_games'])
        else:
            print(f"Adding new entry for {game_name}...")
            # Add new row with basic data
            new_row = [
                game_name,  # title
                '',        # url
                '',        # imgUrl
                page_name, # page
                '',        # custom_redirect
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
            row_index = len(worksheet.col_values(1))  # Get the new row index
            
            # Update related games if present
            if related_data:
                update_related_games(worksheet, row_index, related_data, column_mapping['related_games'])

    except Exception as e:
        print(f"Error updating spreadsheet: {e}")
        return False
        
    return True

def generate_game_content(title, column=None):
    """Generate requested content for a game title."""
    summary = full_text = category = potential_categories = related_data = None
    
    if not column or column == 'summary':
        print("Getting TTRPG summary...")
        summary = get_ttrpg_summary(title)
    
    if not column or column == 'full_text':
        print("Getting full text description...")
        full_text = get_ttrpg_full_text(title)
    
    if not column or column == 'category':
        print("Getting category...")
        category = get_ttrpg_category(title)
    
    if not column or column == 'potential_categories':
        print("Getting potential categories...")
        potential_categories = get_potential_categories(title)
    
    if not column or column == 'related_games':
        print("Getting related games...")
        if not category:
            category = get_ttrpg_category(title)
            
        worksheet = get_worksheet()
        related_games = find_related_games_by_ai(worksheet, title)
        
        related_data = []
        for game in related_games:
            blurb = generate_relationship_blurb(title, game['title'], game['categories'])
            related_data.append({
                'title': game['title'],
                'imgUrl': game['imgUrl'],
                'page': game['page'],
                'blurb': blurb
            })
        while len(related_data) < 3:
            related_data.append({'title': '', 'imgUrl': '', 'page': '', 'blurb': ''})
    
    return summary, full_text, category, potential_categories, related_data


def main():
    parser = argparse.ArgumentParser(
        description='Generate and manage TTRPG game information in a Google Spreadsheet.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single game with all columns
  python ttrpg_blurb_writer.py "Dungeons & Dragons"
  
  # Update only the summary for a game
  python ttrpg_blurb_writer.py "Pathfinder" -c summary
  
  # Update related games for all entries
  python ttrpg_blurb_writer.py --update-all -c related_games
  
Column Descriptions:
  summary              - A 2-3 sentence overview of the game
  full_text           - Detailed HTML-formatted description with multiple sections
  category            - 4-7 categories from predefined lists (genres, themes, mechanics)
  potential_categories - 2-3 suggested new categories not in the predefined lists
  related_games       - Find and describe 2 similar games from the database
        """)
    
    parser.add_argument('game_name', nargs='*', help='Name of the TTRPG game (if not using --update-all)')
    parser.add_argument('--column', '-c', 
                        choices=['summary', 'full_text', 'category', 'potential_categories', 'related_games'],
                        help='Specific column to update (updates all columns if not specified)')
    parser.add_argument('--update-all', action='store_true',
                        help='Update all games in the spreadsheet instead of a single game')
    
    args = parser.parse_args()

    if args.update_all:
        worksheet = get_worksheet()
        titles = [t for t in worksheet.col_values(1)[1:] if t.strip()]
        
        for i, title in enumerate(titles):
            print(f"\nProcessing {i+1}/{len(titles)}: {title}")
            try:
                content = generate_game_content(title, args.column)
                update_google_sheet("TTRPG Directory", title, *content, args.column)
                # Add a small delay between operations
                time.sleep(1)
            except Exception as e:
                print(f"Error processing {title}: {str(e)}")
                continue
        
        print("\nBatch update completed!")
        return  # Exit after completing update_all

    # Single game processing
    ttrpg_name = ' '.join(args.game_name) if args.game_name else input("Enter the name of the TTRPG: ").strip()
    if not ttrpg_name:
        print("Please provide a valid name.")
        return

    print(f"Processing: {ttrpg_name}")
    content = generate_game_content(ttrpg_name, args.column)
    update_google_sheet("TTRPG Directory", ttrpg_name, *content, args.column)
    print("Successfully uploaded the data to Google Sheet!")

if __name__ == "__main__":
    main()
