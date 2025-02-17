from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
from services.sheets_service import SheetsService
import json

load_dotenv()

async def main():
    # Initialize services
    sheets_service = SheetsService()
    genres, themes, mechanics = sheets_service.categories
    
    # Combine all categories
    all_categories = genres + themes + mechanics
    
    # Define start and end categories
    start_category = "Space Opera"
    end_category = "Sword-and-Sorcery"
    
    # Get slice of categories between start and end (inclusive)
    start_index = all_categories.index(start_category)
    end_index = all_categories.index(end_category) + 1  # +1 to include the end category
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
        - Save the post URL
        - Move to the next category
    3. Add the Category/URL for each category to the bottom of this sheet:
        - https://docs.google.com/spreadsheets/d/1G5iyUAnShu48djR8cf7B7CX40NzEWQLrv5HreJM-P8o/edit?gid=0#gid=0
    
    ### Important Notes:
    - Only collect posts that are not Archived ("Archived post. New comments cannot be posted and votes cannot be cast.")
    - Save each URL with its corresponding category, in csv format
    - If a category search yields no results, note it and continue to the next
    
    ### Expected Output:
    A collection of URLs mapped to their categories, in csv format
    """
    
    # Initialize agent with the comprehensive task
    agent = Agent(
        llm=ChatOpenAI(model="gpt-4o"),
        task=task
    )
    
    # Run the agent
    try:
        result = await agent.run()
        
        # Process and save results
        results = {}
        if result:
            # Parse the result text into a dictionary
            # Expected format: "Category, URL: url\nCategory, URL: url"
            for line in str(result).strip().split('\n'):
                if ',' in line and 'URL:' in line:
                    category, url_part = line.split(', URL:', 1)
                    results[category.strip()] = url_part.strip()
                    print(f"Found URL for {category}: {url_part.strip()}")
        
        # Convert results to proper JSON format
        json_output = {
            "categories": [
                {
                    "name": category,
                    "url": url
                }
                for category, url in results.items()
            ]
        }
        
        # Save results to file
        with open('reddit_categories.json', 'w') as f:
            json.dump(json_output, f, indent=4)
        
        print(f"Processed {len(results)} categories. Results saved to reddit_categories.json")
    
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 