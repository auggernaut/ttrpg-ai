import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent, Controller
from langchain_openai import ChatOpenAI
from services.sheets_service import SheetsService
import asyncio
from dotenv import load_dotenv
import csv

load_dotenv()

# Initialize controller
controller = Controller()

@controller.action('Save Reddit category URLs to file')
def save_category_url(category: str, url: str):
    with open('browser_use/reddit_categories.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([category, url])
    return f'Saved URL for {category}'

async def main():
    # Initialize services
    sheets_service = SheetsService()
    genres, themes, mechanics = sheets_service.categories
    
    # Combine all categories
    all_categories = genres + themes + mechanics
    
    # Define start and end categories
    start_category = "Aliens"
    end_category = "Card-Based / Diceless"
    
    # Get slice of categories between start and end (inclusive)
    start_index = all_categories.index(start_category)
    end_index = all_categories.index(end_category) + 1
    categories_to_process = all_categories[start_index:end_index]
    
    # Create a structured task with filtered categories
    task = f"""
    ### Reddit TTRPG Category Search Task

    **Objective:** 
    Search Reddit for various TTRPG categories and collect post URLs that have active comments.

    ### Categories to Search:
    {', '.join(categories_to_process)}

    ### Steps:
    1. Start at https://www.reddit.com
    2. For each category in the list:
        - Search for "[category] ttrpg"
        - Find the first post that has comments enabled
        - Use the 'Save Reddit category URLs to file' action to save the category and URL
        - Move to the next category

    ### Important Notes:
    - Only collect posts that are not Archived ("Archived post. New comments cannot be posted and votes cannot be cast.")
    - If a category search yields no results, note it and continue to the next
    """
    
    # Initialize agent with the comprehensive task and controller
    agent = Agent(
        llm=ChatOpenAI(model="gpt-4o"),
        task=task,
        controller=controller
    )
    
    # Run the agent
    try:
        await agent.run(max_steps=1000)
        print("Processing complete. Results saved to reddit_categories.csv")
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 