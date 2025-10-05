from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id
import structlog

router = Router()
logger = structlog.get_logger(__name__)


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Handle /settings command"""
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        if not user:
            await message.answer("❌ Пользователь не найден. Используй /start")
            return

        gender_emoji = "👨" if user.gender == "male" else "👩" if user.gender == "female" else "❓"
        gender_text = "Мужской" if user.gender == "male" else "Женский" if user.gender == "female" else "Не указан"

        settings_text = f"""⚙️ <b>Настройки профиля</b>

<b>Пол:</b> {gender_emoji} {gender_text}

Пол влияет на стиль анализа и формулировку вопросов для более точного решения проблем."""

        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Изменить пол", callback_data="change_gender")
        builder.adjust(1)

        await message.answer(
            settings_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "change_gender")
async def handle_change_gender(callback: CallbackQuery):
    """Handle gender change request"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👨 Мужской", callback_data="set_gender_male")
    builder.button(text="👩 Женский", callback_data="set_gender_female")
    builder.button(text="◀️ Назад", callback_data="back_to_settings")
    builder.adjust(2, 1)

    await callback.message.edit_text(
        "Выбери свой пол:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_gender_"))
async def handle_set_gender(callback: CallbackQuery):
    """Handle gender setting"""
    new_gender = "male" if callback.data == "set_gender_male" else "female"

    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.gender = new_gender
            await session.commit()
            logger.info(f"User {user.telegram_id} changed gender to: {new_gender}")

    gender_text = "мужской" if new_gender == "male" else "женский"
    await callback.message.edit_text(
        f"✅ Пол изменён на {gender_text}!\n\n"
        f"Теперь анализ проблем будет адаптирован под твой стиль."
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_settings")
async def handle_back_to_settings(callback: CallbackQuery):
    """Go back to settings menu"""
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)

        if not user:
            await callback.message.edit_text("❌ Пользователь не найден. Используй /start")
            await callback.answer()
            return

        gender_emoji = "👨" if user.gender == "male" else "👩" if user.gender == "female" else "❓"
        gender_text = "Мужской" if user.gender == "male" else "Женский" if user.gender == "female" else "Не указан"

        settings_text = f"""⚙️ <b>Настройки профиля</b>

<b>Пол:</b> {gender_emoji} {gender_text}

Пол влияет на стиль анализа и формулировку вопросов для более точного решения проблем."""

        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Изменить пол", callback_data="change_gender")
        builder.adjust(1)

        await callback.message.edit_text(
            settings_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
