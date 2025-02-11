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