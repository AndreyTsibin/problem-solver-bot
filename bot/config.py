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
