import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Scraping Configuration
UPDATE_INTERVAL = 300  # 5 minutes in seconds
MAX_RETRIES = 3
RETRY_DELAY = 60  # 1 minute in seconds
