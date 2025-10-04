import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.database.engine import init_db
from bot.handlers import start, problem_flow, history, payment, referral, subscription, settings
from bot.middleware.errors import ErrorHandlingMiddleware
from bot.services.subscription_renewal import start_renewal_scheduler

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
    logger.info("Error handling middleware initialized")

    # Register routers
    dp.include_router(start.router)
    dp.include_router(problem_flow.router)
    dp.include_router(history.router)
    dp.include_router(payment.router)
    dp.include_router(referral.router)
    dp.include_router(subscription.router)
    dp.include_router(settings.router)
    logger.info("All routers registered")

    # Start subscription renewal scheduler as background task
    renewal_task = asyncio.create_task(start_renewal_scheduler(bot))
    logger.info("Subscription renewal scheduler started")

    # Start polling
    logger.info("Bot started successfully! Press Ctrl+C to stop.")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        renewal_task.cancel()  # Stop renewal scheduler
        try:
            await renewal_task
        except asyncio.CancelledError:
            logger.info("Renewal scheduler stopped")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
