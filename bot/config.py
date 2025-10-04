import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# YooKassa payment settings
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# Validate required settings
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file")
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY is not set in .env file")
if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
    raise ValueError("YOOKASSA credentials are not set in .env file")

# Free tier limits
FREE_SOLUTIONS = 1  # Free problem solutions per user (optimized for conversion)
FREE_DISCUSSION_QUESTIONS = 5  # Base question limit for all users

# Package limits for paid users
STARTER_DISCUSSION_LIMIT = 10  # Additional questions for Starter package
MEDIUM_DISCUSSION_LIMIT = 15   # Additional questions for Medium package
LARGE_DISCUSSION_LIMIT = 25    # Additional questions for Large package

# Subscription plans (monthly recurring)
SUBSCRIPTION_PLANS = {
    'standard': {
        'price': 299,  # Telegram Stars (~599₽)
        'solutions_per_month': 15,
        'discussion_limit': 15,
        'name': 'Стандарт'
    },
    'premium': {
        'price': 499,  # Telegram Stars (~999₽)
        'solutions_per_month': 30,
        'discussion_limit': 25,
        'name': 'Премиум'
    }
}

# Payment providers configuration
ENABLE_YOOKASSA = True  # YooKassa payments (rubles, Russian cards)
ENABLE_TELEGRAM_STARS = True  # Telegram Stars (international payments)

# Pricing for Telegram Stars (in stars, ~2₽ per star)
PACKAGES_STARS = {
    'starter': {'solutions': 5, 'price': 125, 'discussion_limit': 10, 'name': 'Стартовый'},
    'medium': {'solutions': 15, 'price': 300, 'discussion_limit': 15, 'name': 'Средний'},
    'large': {'solutions': 30, 'price': 600, 'discussion_limit': 25, 'name': 'Большой'},
    'discussion_5': {'discussions': 5, 'price': 50, 'name': '5 вопросов'},
    'discussion_15': {'discussions': 15, 'price': 120, 'name': '15 вопросов'},
    'subscription_standard': {'solutions': 15, 'price': 299, 'discussion_limit': 15, 'plan': 'standard', 'name': 'Подписка Стандарт'},
    'subscription_premium': {'solutions': 30, 'price': 499, 'discussion_limit': 25, 'plan': 'premium', 'name': 'Подписка Премиум'},
}

# Pricing for YooKassa (in rubles)
PACKAGES_YOOKASSA = {
    'starter': {'solutions': 5, 'price': 250, 'discussion_limit': 10, 'name': 'Стартовый'},
    'medium': {'solutions': 15, 'price': 600, 'discussion_limit': 15, 'name': 'Средний'},
    'large': {'solutions': 30, 'price': 1200, 'discussion_limit': 25, 'name': 'Большой'},
    'discussion_5': {'discussions': 5, 'price': 100, 'name': '5 вопросов'},
    'discussion_15': {'discussions': 15, 'price': 240, 'name': '15 вопросов'},
    'subscription_standard': {'solutions': 15, 'price': 599, 'discussion_limit': 15, 'plan': 'standard', 'name': 'Подписка Стандарт'},
    'subscription_premium': {'solutions': 30, 'price': 999, 'discussion_limit': 25, 'plan': 'premium', 'name': 'Подписка Премиум'},
}
