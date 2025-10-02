import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validate required settings
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file")
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY is not set in .env file")

# Free tier limits
FREE_SOLUTIONS = 3  # Free problem solutions per user (increased from 1)
FREE_DISCUSSION_QUESTIONS = 5  # Base question limit for all users

# Package limits for paid users
STARTER_DISCUSSION_LIMIT = 10  # Additional questions for Starter package
MEDIUM_DISCUSSION_LIMIT = 15   # Additional questions for Medium package
LARGE_DISCUSSION_LIMIT = 25    # Additional questions for Large package
