from config.constants import openai_client, GPT_MODEL
from utils.decorators import retry_with_backoff
from services.sheets_service import SheetsService

class OpenAIService:
    def __init__(self):
        self.sheets_service = SheetsService()
        self.genres, self.themes, self.mechanics = self.sheets_service.categories
        self.categories = self.genres + self.themes + self.mechanics

    @staticmethod
    @retry_with_backoff
    def get_ttrpg_summary(game_name, notes=None):
        notes_text = f"\nAdditional context about the game:\n{notes}" if notes else ""
        
        prompt = f"""Write a short, engaging blurb about the tabletop roleplaying game '{game_name}'. 
    Include its theme, key features, and what makes it unique. Keep it between 2-3 sentences. It should read more like an explanation of the game and not an advertisement.{notes_text}

    Here are some examples of the style I'm looking for:

    For "Blades in the Dark":
    Blades in the Dark offers a gripping foray into a Victorian-inspired, ghost-infested city where players lead a crew of criminals undertaking high-stakes heists. The game stands out with its narrative-driven, team-based mechanics and a unique cycle of action and consequence that challenges players to think strategically and cooperate effectively.

    For "Dungeon World":
    Dungeon World is a streamlined tabletop RPG that focuses on storytelling and character development within a classic fantasy setting. It uses simple mechanics derived from the Powered by the Apocalypse system, facilitating fast-paced, collaborative storytelling. The game emphasizes player choices and narrative consequences, making it an excellent choice for those who value creative freedom and dynamic, character-driven adventures.

    Please write a similar style blurb for: {game_name}"""

        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    @retry_with_backoff
    def get_ttrpg_full_text(game_name, notes=None):
        notes_text = f"\nAdditional context about the game:\n{notes}" if notes else ""
        
        prompt = f"""Write a detailed description of the tabletop roleplaying game '{game_name}' formatted in HTML using <article> and <section> blocks. Include its theme, rules overview, unique mechanics, and target audience.{notes_text}

    Important:
    - Do not use <h1> tags. Start your sections with <h2> if headings are needed
    - The output should start and end with <article> tags
    - Do not wrap the response in any markdown or code blocks
    - Provide only the raw HTML content

    The description should cover:
    - Theme and setting
    - Core mechanics
    - What makes it unique
    - Target audience"""

        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        
        # Remove any markdown code block formatting if present
        content = response.choices[0].message.content.strip()
        content = content.replace('```html', '').replace('```', '')
        return content.strip()

    @retry_with_backoff
    def get_ttrpg_category(self, game_name):
        genres_string = '; '.join(self.genres)
        themes_string = '; '.join(self.themes)
        mechanics_string = '; '.join(self.mechanics)
        
        prompt = f"""Analyze the tabletop roleplaying game '{game_name}' and select 4-7 categories total from the following lists. Choose categories that best capture the game's core essence and unique features. Provide the categories separated by a semicolon and space.

    Requirements:
    - Must include at least one GENRE
    - Must include at least one THEME
    - Must include at least one MECHANIC/SYSTEM
    - Total categories should be between 4 and 8
    - List most important categories first

    GENRES: {genres_string}

    THEMES: {themes_string}

    MECHANICS & SYSTEMS: {mechanics_string}

    Example responses:
    - For D&D 5E: Fantasy; High-Fantasy; Class-based; Character Customization; Tactical Combat; Team-Based
    - For Blades in the Dark: Dark Fantasy; Gothic; Dark; Heist; Narrative-Driven; Team-Based

    Important: Select only the categories that truly define the game's core identity, ordered by importance."""

        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        
        # Get response and split into categories
        categories = response.choices[0].message.content.strip().split('; ')
        
        # Filter out any categories that aren't in our defined sets
        valid_categories = [
            cat for cat in categories 
            if cat in self.genres 
            or cat in self.themes 
            or cat in self.mechanics
        ]
        
        # Join back into semicolon-separated string
        return '; '.join(valid_categories)

    @retry_with_backoff
    def get_potential_categories(self, game_name):
        prompt = f"""Analyze the tabletop roleplaying game '{game_name}' and suggest 2-3 new potential categories or tags that aren't in the following list. 
    These should be unique, specific categories that could be useful for categorizing this and similar games. Format your response as a semicolon-separated list.

    Existing categories: {'; '.join(self.categories)}"""

        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    
    @staticmethod
    @retry_with_backoff
    def find_related_games_by_ai(worksheet, current_game):
        try:
            # Get all game titles and their categories
            all_data = worksheet.get_all_records()
            games_with_categories = [
                {'title': row['title'], 'categories': row.get('Category', '')} 
                for row in all_data 
                if row['title'].lower() != current_game.lower()
            ]
            
            # Create prompt for AI
            games_info = '\n'.join([
                f"- {game['title']} ({game['categories']})" 
                for game in games_with_categories[:100]  # Limit to first 100 games
            ])
            
            prompt = f"""Given the tabletop RPG "{current_game}", identify 3 related but distinctly different games from the list below. 
    Each recommendation should offer a unique perspective or alternative approach while maintaining some connection to {current_game}.

    Games and their categories:
    {games_info}

    Requirements:
    - Choose games with different mechanical approaches or unique twists
    - Avoid selecting games that are too similar to each other
    - Consider both obvious and non-obvious connections
    - Focus on games that would interest players of {current_game} but offer fresh experiences

    Format your response as a semicolon-separated list of exactly 3 games. Example: "Game1; Game2; Game3"
    Important: Only include games from the provided list. You must return exactly 3 games."""

            response = openai_client.chat.completions.create(
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

    @staticmethod
    @retry_with_backoff
    def generate_relationship_blurb(game1_name, game2_name, game2_categories):
        prompt = f"""Write a brief 1-2 sentence description of how the tabletop RPG "{game2_name}" relates to "{game1_name}". 
    Focus on their shared elements or complementary features, especially how they differ in play style and game mechanics. Also an example of how they differ.
    Wrap any titles in <i> tags.
    Categories for {game2_name}: {game2_categories}"""

        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    
    @staticmethod
    @retry_with_backoff
    def extract_reviews(text_content):
        prompt = f"""
        Extract all user reviews from the following text:

        {text_content}

        Provide each review in a separate line.

        Reviews:
        """
        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
            temperature=0
        )
        reviews_text = response.choices[0].message.content
        reviews = reviews_text.strip().split('\n')
        return reviews
    
    @staticmethod
    @retry_with_backoff
    def summarize_reviews(reviews):
        combined_reviews = ' '.join(reviews)
        prompt = f"""
        Summarize the following user reviews into a concise paragraph highlighting the main points:

        {combined_reviews}

        Summary:
        """
        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
            temperature=0.0
        )
        summary = response.choices[0].message.content
        return summary.strip()