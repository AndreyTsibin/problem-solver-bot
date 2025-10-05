"""Profile management handlers"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user
from bot.handlers.start import calculate_age
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    """Show user profile with all information"""
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id
        from bot.database.crud_subscriptions import get_referral_stats

        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используй /start")
            return

        # Calculate age from birth_date
        age_text = f"{calculate_age(user.birth_date)} лет" if user.birth_date else "не указан"

        # Get referral stats
        stats = await get_referral_stats(session, user.id)

        # Get bot username for referral link
        bot_me = await message.bot.me()
        referral_link = f"https://t.me/{bot_me.username}?start=ref_{user.referral_code}"

        # Work format display
        work_format_emoji = {
            'remote': '🏠',
            'office': '🏢',
            'hybrid': '🔀',
            'student': '🎓'
        }.get(user.work_format, '')

        work_format_text = {
            'remote': 'Удаленно',
            'office': 'В офисе',
            'hybrid': 'Гибрид',
            'student': 'Учусь/не работаю'
        }.get(user.work_format, 'не указан')

        text = f"""👤 Твой профиль

📊 Личные данные:
• Пол: {'Мужской' if user.gender == 'male' else 'Женский' if user.gender == 'female' else 'не указан'}
• Возраст: {age_text}
• Занятость: {user.occupation or 'не указана'}
• Формат работы: {work_format_emoji} {work_format_text}

💳 Баланс:
• Решений осталось: {user.problems_remaining}
• Вопросов для обсуждения: {user.discussion_credits}

🎁 Реферальная программа:
• Приглашено друзей: {stats['total_referrals']}
• Получено бонусов: {stats['total_rewards']} решений

Твоя ссылка: <code>{referral_link}</code>"""

        builder = InlineKeyboardBuilder()
        builder.button(text="✏️ Изменить данные", callback_data="edit_profile")
        builder.button(text="📖 История решений", callback_data="show_history")
        builder.button(text="💳 Пополнить баланс", callback_data="show_payment_options")
        builder.button(text="📋 Скопировать ссылку", callback_data="copy_referral_link")
        builder.adjust(1)

        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "show_payment_options")
async def show_payment_options(callback: CallbackQuery):
    """Show payment options (subscriptions/packages/discussions)"""
    text = """💳 <b>Что тебе удобнее?</b>

<b>📅 Подписка</b>
• Автопродление каждый месяц
• Не нужно каждый раз покупать
• Выгоднее при регулярном использовании

<b>💰 Разовые пакеты</b>
• Покупаешь один раз
• Решения не сгорают
• Используешь когда удобно

<b>💬 Вопросы для обсуждения</b>
• Дополнительные вопросы после решения
• Для более глубокого анализа"""

    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Подписки", callback_data="show_subscriptions")
    builder.button(text="💰 Разовые пакеты", callback_data="show_packages")
    builder.button(text="💬 Вопросы для обсуждения", callback_data="buy_discussions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "show_history")
async def show_history_from_profile(callback: CallbackQuery):
    """Show user's problem history"""
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id, get_user_problems

        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        problems = await get_user_problems(session, user.id, limit=10)

        if not problems:
            await callback.message.edit_text("📭 У тебя пока нет решённых задач")
            await callback.answer()
            return

        builder = InlineKeyboardBuilder()
        for p in problems:
            status_emoji = "✅" if p.status == "solved" else "⏳"
            title = p.title[:40] + "..." if len(p.title) > 40 else p.title
            builder.button(
                text=f"{status_emoji} {title}",
                callback_data=f"view_problem_{p.id}"
            )
        builder.button(text="◀️ Назад в профиль", callback_data="back_to_profile")
        builder.adjust(1)

        await callback.message.edit_text(
            "📖 История решений:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()


@router.callback_query(F.data == "copy_referral_link")
async def copy_referral_link(callback: CallbackQuery):
    """Copy referral link notification"""
    await callback.answer(
        "Ссылка уже в сообщении выше! Просто нажми на неё и скопируй",
        show_alert=True
    )


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery):
    """Go back to profile view"""
    # Re-trigger show_profile logic via pseudo-message
    # For now, just tell user to click profile button again
    await callback.message.edit_text(
        "Для возврата в профиль нажми кнопку 👤 Профиль в меню внизу"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: CallbackQuery):
    """Show what user can edit"""
    text = "✏️ Что хочешь изменить?"

    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Дата рождения", callback_data="edit_birth_date")
    builder.button(text="💼 Занятость", callback_data="edit_occupation")
    builder.button(text="🏠 Формат работы", callback_data="edit_work_format")
    builder.button(text="👤 Пол", callback_data="edit_gender")
    builder.button(text="◀️ Назад", callback_data="back_to_profile")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


# TODO: Implement edit handlers for each field (will be added in next iteration)
