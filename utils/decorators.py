import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Any
from gspread.exceptions import APIError
from openai import APIError as OpenAIAPIError, RateLimitError
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_with_backoff(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                if attempt == max_attempts:
                    raise e
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
    return decorator
