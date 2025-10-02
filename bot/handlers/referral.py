"""Referral system handlers"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user
from bot.database.crud_subscriptions import create_referral_code, get_referral_stats
import structlog

logger = structlog.get_logger()
router = Router()


@router.message(Command("referral"))
async def handle_referral_command(message: Message):
    """Handle /referral command - show referral stats and link"""
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name or "Пользователь"

    try:
        async with AsyncSessionLocal() as session:
            # Get or create user
            user = await get_or_create_user(
                session, telegram_id, username, first_name
            )

            # Generate or get existing referral code
            referral_code = await create_referral_code(session, user.id)

            # Get referral statistics
            stats = await get_referral_stats(session, user.id)

            # Get bot username for referral link
            bot_me = await message.bot.me()
            bot_username = bot_me.username
            referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}"

            # Format message
            text = (
                f"🎁 <b>Реферальная программа</b>\n\n"
                f"Приглашай друзей и получай бонусы!\n\n"
                f"👥 <b>Твоя статистика:</b>\n"
                f"• Приглашено друзей: {stats['total_referrals']}\n"
                f"• Получено бонусов: +{stats['total_rewards']} решений\n\n"
                f"🎯 <b>Условия:</b>\n"
                f"• Твой друг получит +1 бонусное решение\n"
                f"• Ты получишь +1 решение за каждого друга\n\n"
                f"🔗 <b>Твоя реферальная ссылка:</b>\n"
                f"<code>{referral_link}</code>\n\n"
                f"Просто отправь эту ссылку другу!"
            )

            # Create share button
            share_text = f"Попробуй МозгоБот - AI-коуч для решения проблем! 🚀\nПолучи +1 бонусное решение по моей ссылке: {referral_link}"
            share_url = f"https://t.me/share/url?url={referral_link}&text={share_text}"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📤 Поделиться с другом",
                    url=share_url
                )]
            ])

            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logger.error("referral_command_error", error=str(e), user_id=telegram_id)
        await message.answer(
            "❌ Произошла ошибка при загрузке реферальной программы. "
            "Попробуйте позже."
        )
