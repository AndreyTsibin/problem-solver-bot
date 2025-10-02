"""Subscription renewal service for automated billing"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.engine import AsyncSessionLocal
from bot.database.models import Subscription, User
from bot.database.crud_subscriptions import renew_subscription, cancel_subscription
from bot.config import SUBSCRIPTION_PLANS
import structlog

logger = structlog.get_logger()


async def check_and_renew_subscriptions(bot):
    """
    Check all active subscriptions and process renewals.

    Note: Telegram Stars API doesn't support automatic recurring payments.
    This function sends renewal reminders to users instead of charging automatically.

    Args:
        bot: Telegram bot instance for sending notifications
    """
    logger.info("Starting subscription renewal check")

    try:
        async with AsyncSessionLocal() as session:
            # Find all active subscriptions
            result = await session.execute(
                select(Subscription).where(Subscription.status == 'active')
            )
            subscriptions = result.scalars().all()

            logger.info(f"Found {len(subscriptions)} active subscriptions")

            for subscription in subscriptions:
                try:
                    await _process_subscription(session, subscription, bot)
                except Exception as e:
                    logger.error(
                        "subscription_processing_error",
                        subscription_id=subscription.id,
                        error=str(e)
                    )

            await session.commit()

    except Exception as e:
        logger.error("subscription_renewal_check_error", error=str(e))


async def _process_subscription(session: AsyncSession, subscription: Subscription, bot):
    """Process a single subscription for renewal"""
    now = datetime.utcnow()

    # Get user for this subscription
    result = await session.execute(
        select(User).where(User.subscription_id == subscription.id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"No user found for subscription {subscription.id}")
        return

    # Calculate days until renewal
    days_until_renewal = (subscription.next_billing_date - now).days

    # Send reminder 3 days before renewal
    if days_until_renewal == 3:
        await _send_renewal_reminder(bot, user, subscription, days=3)
        logger.info(f"Sent 3-day reminder to user {user.telegram_id}")

    # Send reminder on renewal day
    elif days_until_renewal == 0:
        await _send_renewal_request(bot, user, subscription)
        logger.info(f"Sent renewal request to user {user.telegram_id}")

    # Auto-cancel 3 days after expiration if not renewed
    elif days_until_renewal == -3:
        await cancel_subscription(session, subscription.id)
        await _send_cancellation_notice(bot, user, subscription)
        logger.info(f"Auto-cancelled subscription for user {user.telegram_id}")


async def _send_renewal_reminder(bot, user: User, subscription: Subscription, days: int):
    """Send renewal reminder to user"""
    plan_name = SUBSCRIPTION_PLANS.get(subscription.plan, {}).get('name', subscription.plan.capitalize())

    text = (
        f"⏰ <b>Напоминание о подписке</b>\n\n"
        f"Твоя подписка <b>{plan_name}</b> истекает через <b>{days} дня</b>.\n\n"
        f"💰 Стоимость продления: {subscription.price} ⭐️\n"
        f"📦 Ты получишь: {subscription.solutions_per_month} решений\n\n"
        f"Чтобы продлить подписку, используй /subscription"
    )

    try:
        await bot.send_message(user.telegram_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send reminder to {user.telegram_id}: {e}")


async def _send_renewal_request(bot, user: User, subscription: Subscription):
    """Send renewal request on expiration day"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    plan_name = SUBSCRIPTION_PLANS.get(subscription.plan, {}).get('name', subscription.plan.capitalize())

    text = (
        f"⚠️ <b>Подписка истекает сегодня!</b>\n\n"
        f"Твоя подписка <b>{plan_name}</b> заканчивается.\n\n"
        f"💰 Продли сейчас за {subscription.price} ⭐️\n"
        f"📦 Получи {subscription.solutions_per_month} решений на следующий месяц\n\n"
        f"Если не продлишь в течение 3 дней, подписка будет отменена автоматически."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💳 Продлить за {subscription.price}⭐️",
            callback_data=f"renew_subscription_{subscription.plan}"
        )],
        [InlineKeyboardButton(
            text="❌ Отменить подписку",
            callback_data="cancel_subscription_confirm"
        )]
    ])

    try:
        await bot.send_message(user.telegram_id, text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send renewal request to {user.telegram_id}: {e}")


async def _send_cancellation_notice(bot, user: User, subscription: Subscription):
    """Send cancellation notice after grace period"""
    plan_name = SUBSCRIPTION_PLANS.get(subscription.plan, {}).get('name', subscription.plan.capitalize())

    text = (
        f"❌ <b>Подписка отменена</b>\n\n"
        f"Твоя подписка <b>{plan_name}</b> была автоматически отменена, "
        f"так как оплата не поступила в течение 3 дней.\n\n"
        f"Ты можешь оформить новую подписку в любой момент: /subscription"
    )

    try:
        await bot.send_message(user.telegram_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send cancellation notice to {user.telegram_id}: {e}")


async def start_renewal_scheduler(bot):
    """Start background task for subscription renewals (runs daily at 03:00 UTC)"""
    logger.info("Starting subscription renewal scheduler")

    while True:
        try:
            # Calculate time until next 03:00 UTC
            now = datetime.utcnow()
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)

            # If it's already past 03:00 today, schedule for tomorrow
            if now.hour >= 3:
                next_run += timedelta(days=1)

            sleep_seconds = (next_run - now).total_seconds()
            logger.info(f"Next renewal check scheduled in {sleep_seconds/3600:.1f} hours at {next_run}")

            # Sleep until next scheduled run
            await asyncio.sleep(sleep_seconds)

            # Run renewal check
            await check_and_renew_subscriptions(bot)

        except asyncio.CancelledError:
            logger.info("Subscription renewal scheduler stopped")
            break
        except Exception as e:
            logger.error("renewal_scheduler_error", error=str(e))
            # Wait 1 hour before retry on error
            await asyncio.sleep(3600)
