# config.py
import os

BASE_URL = "https://www.fastprotocol.io"
API_TIMEOUT = 30
RATE_LIMIT_DELAY = 0.5  # seconds between requests
MAX_RETRIES = 3
MAX_USERS_PER_ENTITY = 1000  # Limit users per entity for faster processing
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
DUNE_API_KEY='sim_2nUBjRsl4R5mY8cHlFORMlbE05rMj9Az'
