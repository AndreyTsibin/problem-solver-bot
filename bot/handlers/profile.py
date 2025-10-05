"""Profile management handlers"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user, get_user_by_telegram_id, calculate_age
from bot.states import ProfileEditStates
from datetime import datetime
import structlog

router = Router()
logger = structlog.get_logger(__name__)


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
        age = calculate_age(user.birth_date) if user.birth_date else None
        age_text = f"{age} лет" if age else "не указан"

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

        # Calculate available discussion questions
        from bot.config import (
            FREE_DISCUSSION_QUESTIONS,
            STARTER_DISCUSSION_LIMIT,
            MEDIUM_DISCUSSION_LIMIT,
            LARGE_DISCUSSION_LIMIT
        )

        base_limits = {
            'starter': STARTER_DISCUSSION_LIMIT,
            'medium': MEDIUM_DISCUSSION_LIMIT,
            'large': LARGE_DISCUSSION_LIMIT
        }
        base_limit = base_limits.get(user.last_purchased_package, FREE_DISCUSSION_QUESTIONS)
        total_discussion_credits = base_limit + user.discussion_credits

        text = f"""👤 Твой профиль

📊 Личные данные:
• Пол: {'Мужской' if user.gender == 'male' else 'Женский' if user.gender == 'female' else 'не указан'}
• Возраст: {age_text}
• Занятость: {user.occupation or 'не указана'}
• Формат работы: {work_format_emoji} {work_format_text}

💳 Баланс:
• Решений осталось: {user.problems_remaining}
• Вопросов для обсуждения: {total_discussion_credits}

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


# Edit handlers for profile fields

@router.callback_query(F.data == "edit_birth_date")
async def edit_birth_date(callback: CallbackQuery, state: FSMContext):
    """Start editing birth date"""
    await state.set_state(ProfileEditStates.editing_birth_date)
    await callback.message.edit_text(
        "📅 Укажи новую дату рождения (ДД.ММ.ГГГГ)\n\n"
        "Например: 15.03.1995"
    )
    await callback.answer()


@router.message(ProfileEditStates.editing_birth_date)
async def save_birth_date_edit(message: Message, state: FSMContext):
    """Save edited birth date"""
    try:
        birth_date = datetime.strptime(message.text, "%d.%m.%Y")

        # Validate age (14-100 years)
        age = calculate_age(birth_date)
        if age < 14 or age > 100:
            await message.answer(
                "⚠️ Укажи реальную дату рождения (возраст от 14 до 100 лет)"
            )
            return

        # Update database
        async with AsyncSessionLocal() as session:
            user = await get_user_by_telegram_id(session, message.from_user.id)
            if user:
                user.birth_date = birth_date
                await session.commit()
                logger.info(f"User {user.telegram_id} updated birth_date: {birth_date}")

        await state.clear()
        await message.answer(
            f"✅ Дата рождения обновлена!\n\n"
            f"Твой возраст: {age} лет\n\n"
            f"Нажми 👤 Профиль чтобы увидеть изменения"
        )

    except ValueError:
        await message.answer(
            "⚠️ Неверный формат!\n\n"
            "Используй формат ДД.ММ.ГГГГ\n"
            "Например: 15.03.1995"
        )


@router.callback_query(F.data == "edit_occupation")
async def edit_occupation(callback: CallbackQuery, state: FSMContext):
    """Start editing occupation"""
    await state.set_state(ProfileEditStates.editing_occupation)
    await callback.message.edit_text(
        "💼 Укажи свою занятость\n\n"
        "Примеры:\n"
        "• Разработчик\n"
        "• Менеджер\n"
        "• Студент\n"
        "• Фрилансер"
    )
    await callback.answer()


@router.message(ProfileEditStates.editing_occupation)
async def save_occupation_edit(message: Message, state: FSMContext):
    """Save edited occupation"""
    occupation = message.text.strip()

    if len(occupation) < 2 or len(occupation) > 100:
        await message.answer("⚠️ Укажи от 2 до 100 символов")
        return

    # Update database
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if user:
            user.occupation = occupation
            await session.commit()
            logger.info(f"User {user.telegram_id} updated occupation: {occupation}")

    await state.clear()
    await message.answer(
        f"✅ Занятость обновлена!\n\n"
        f"Ты указал(а): {occupation}\n\n"
        f"Нажми 👤 Профиль чтобы увидеть изменения"
    )


@router.callback_query(F.data == "edit_work_format")
async def edit_work_format(callback: CallbackQuery, state: FSMContext):
    """Start editing work format"""
    await state.set_state(ProfileEditStates.editing_work_format)

    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Удалённо", callback_data="work_remote_edit")
    builder.button(text="🏢 В офисе", callback_data="work_office_edit")
    builder.button(text="🔀 Гибрид", callback_data="work_hybrid_edit")
    builder.button(text="🎓 Учусь/не работаю", callback_data="work_student_edit")
    builder.adjust(1)

    await callback.message.edit_text(
        "🏠 Выбери формат работы:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.in_(["work_remote_edit", "work_office_edit", "work_hybrid_edit", "work_student_edit"]))
async def save_work_format_edit(callback: CallbackQuery, state: FSMContext):
    """Save edited work format"""
    work_format_map = {
        'work_remote_edit': 'remote',
        'work_office_edit': 'office',
        'work_hybrid_edit': 'hybrid',
        'work_student_edit': 'student'
    }

    work_format = work_format_map.get(callback.data)
    if not work_format:
        await callback.answer("❌ Неизвестный формат", show_alert=True)
        return

    # Update database
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.work_format = work_format
            await session.commit()
            logger.info(f"User {user.telegram_id} updated work_format: {work_format}")

    await state.clear()

    work_format_text = {
        'remote': '🏠 Удалённо',
        'office': '🏢 В офисе',
        'hybrid': '🔀 Гибрид',
        'student': '🎓 Учусь/не работаю'
    }.get(work_format, work_format)

    await callback.message.edit_text(
        f"✅ Формат работы обновлён!\n\n"
        f"Ты выбрал(а): {work_format_text}\n\n"
        f"Нажми 👤 Профиль чтобы увидеть изменения"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_gender")
async def edit_gender(callback: CallbackQuery, state: FSMContext):
    """Start editing gender"""
    await state.set_state(ProfileEditStates.editing_gender)

    builder = InlineKeyboardBuilder()
    builder.button(text="👨 Мужской", callback_data="gender_male_edit")
    builder.button(text="👩 Женский", callback_data="gender_female_edit")
    builder.adjust(2)

    await callback.message.edit_text(
        "👤 Выбери пол:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.in_(["gender_male_edit", "gender_female_edit"]))
async def save_gender_edit(callback: CallbackQuery, state: FSMContext):
    """Save edited gender"""
    gender = 'male' if callback.data == 'gender_male_edit' else 'female'

    # Update database
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.gender = gender
            await session.commit()
            logger.info(f"User {user.telegram_id} updated gender: {gender}")

    await state.clear()

    gender_text = '👨 Мужской' if gender == 'male' else '👩 Женский'

    await callback.message.edit_text(
        f"✅ Пол обновлён!\n\n"
        f"Ты указал(а): {gender_text}\n\n"
        f"Нажми 👤 Профиль чтобы увидеть изменения"
    )
    await callback.answer()
