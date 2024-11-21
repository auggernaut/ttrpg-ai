from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize constants
GPT_MODEL = "gpt-4o-mini"
SERVICE_ACCOUNT_FILE = 'ttrpg-games-9a5bfcb02194.json'

# Initialize the client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Move all your category lists here

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
CATEGORIES = GENRES + THEMES + MECHANICS