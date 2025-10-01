import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.database.engine import init_db
from bot.handlers import start, problem_flow, history, payment
from bot.middleware.errors import ErrorHandlingMiddleware

# Configure structured logging with both file and console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main bot function"""
    # Initialize database
    logger.info("Initializing database...")
    await init_db()

    # Create bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # Register error handling middleware
    dp.update.middleware(ErrorHandlingMiddleware())
    logger.info("Error handling middleware registered")

    # Register routers
    dp.include_router(start.router)
    dp.include_router(problem_flow.router)
    dp.include_router(history.router)
    dp.include_router(payment.router)

    # Start polling
    logger.info("Bot started successfully! Press Ctrl+C to stop.")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
