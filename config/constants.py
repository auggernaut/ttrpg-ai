import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize constants
GPT_MODEL = "gpt-4o"
SERVICE_ACCOUNT_FILE = 'ttrpg-games-212e54b63af3.json'

# Initialize the client
custom_httpx_client = httpx.Client(proxy=None)
openai_client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=custom_httpx_client
)