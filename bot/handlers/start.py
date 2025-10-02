from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user
from bot.keyboards import get_main_menu_keyboard
import logging
import asyncio
from datetime import datetime, timedelta

router = Router()
logger = logging.getLogger(__name__)

# Track last /start call per user to prevent duplicates
_last_start_calls = {}
_THROTTLE_SECONDS = 2


def _get_solutions_word(count: int) -> str:
    """Get correct Russian word form for 'решение' based on count"""
    if count % 10 == 1 and count % 100 != 11:
        return "решение"
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return "решения"
    else:
        return "решений"


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    user_id = message.from_user.id
    now = datetime.now()

    # Check if we recently handled /start for this user (throttling)
    if user_id in _last_start_calls:
        time_since_last = (now - _last_start_calls[user_id]).total_seconds()
        if time_since_last < _THROTTLE_SECONDS:
            logger.info(f"Ignoring duplicate /start from user {user_id} (called {time_since_last:.2f}s ago)")
            return

    # Update last call time
    _last_start_calls[user_id] = now

    logger.info(f"cmd_start called for user {message.from_user.id} (@{message.from_user.username})")
    logger.info(f"Message text: '{message.text}', Message ID: {message.message_id}")

    # Get or create user in database
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )

    # Welcome message
    welcome_text = f"""👋 Привет, {message.from_user.first_name}!

Я твой личный коуч по решению проблем. Помогу разобраться в любой ситуации и найти реальное решение.

💬 **Что я умею:**
• Задаю правильные вопросы, которые помогают увидеть суть
• Нахожу корневую причину, а не просто симптомы
• Даю конкретный план действий с дедлайнами

🎯 **С чем помогаю:**
Работа, отношения, здоровье, привычки, финансы, карьера — любая проблема, где нужна ясность и план.

⚡ **Как работаем:**
1. Ты описываешь проблему (2-3 предложения)
2. Я задаю 3-5 уточняющих вопросов
3. Ты получаешь решение с конкретными шагами

💳 **У тебя есть:** {user.problems_remaining} {_get_solutions_word(user.problems_remaining)}

Используй меню внизу для навигации! 👇"""

    logger.info(f"Sending welcome message to user {message.from_user.id}")
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard()
    )
    logger.info(f"Welcome message sent to user {message.from_user.id}")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """📚 **Как работать с ботом:**

1️⃣ Нажми "🚀 Решить проблему"
2️⃣ Опиши проблему своими словами (2-3 предложения)
3️⃣ Отвечай на мои вопросы — я задам 3-5 штук
4️⃣ Получи готовое решение с планом действий

💡 **Примеры проблем, с которыми помогаю:**

🏃 Привычки и здоровье
"Не могу заставить себя заниматься спортом"
"Постоянно переедаю вечером"

💼 Работа и карьера
"Выгораю на работе, нет мотивации"
"Не знаю куда развиваться дальше"

💰 Финансы
"Деньги утекают сквозь пальцы"
"Не могу начать откладывать"

👥 Отношения
"Постоянные конфликты с партнёром"
"Не могу установить границы"

✅ **Чтобы получить максимум:**
• Опиши конкретную ситуацию, а не общую тему
• Отвечай честно — это анонимно и конфиденциально
• Не спеши, вдумчиво отвечай на вопросы

🎁 **У тебя 3 бесплатных решения** — попробуй прямо сейчас!"""

    await message.answer(help_text, reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Handle help button press (legacy inline button)"""
    help_text = """📚 **Как работать с ботом:**

1️⃣ Нажми "🚀 Решить проблему" в меню
2️⃣ Опиши проблему своими словами (2-3 предложения)
3️⃣ Отвечай на мои вопросы — я задам 3-5 штук
4️⃣ Получи готовое решение с планом действий

💡 **Примеры проблем, с которыми помогаю:**

🏃 Привычки и здоровье
"Не могу заставить себя заниматься спортом"
"Постоянно переедаю вечером"

💼 Работа и карьера
"Выгораю на работе, нет мотивации"
"Не знаю куда развиваться дальше"

💰 Финансы
"Деньги утекают сквозь пальцы"
"Не могу начать откладывать"

👥 Отношения
"Постоянные конфликты с партнёром"
"Не могу установить границы"

✅ **Чтобы получить максимум:**
• Опиши конкретную ситуацию, а не общую тему
• Отвечай честно — это анонимно и конфиденциально
• Не спеши, вдумчиво отвечай на вопросы

🎁 **У тебя 3 бесплатных решения** — попробуй прямо сейчас!"""

    await callback.message.answer(help_text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


# Text button handlers for persistent keyboard
@router.message(F.text == "🚀 Решить проблему")
async def menu_new_problem(message: Message, state: FSMContext):
    """Handle 'New Problem' menu button"""
    from bot.states import ProblemSolvingStates

    # Check user limits
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )

        if user.problems_remaining <= 0:
            builder = InlineKeyboardBuilder()
            builder.button(text="💳 Купить решения", callback_data="buy_solutions")
            builder.adjust(1)

            await message.answer(
                "❌ У тебя закончились решения!\n\n"
                "💳 Купи пакет решений, чтобы продолжить анализ проблем.",
                reply_markup=builder.as_markup()
            )
            return

    await message.answer(
        "🎯 Опиши свою проблему в 2-3 предложениях.\n\n"
        "Что происходит и почему это важно решить?"
    )
    await state.set_state(ProblemSolvingStates.waiting_for_problem)


@router.message(F.text == "📖 История")
async def menu_history(message: Message):
    """Handle 'History' menu button"""
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id, get_user_problems

        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используй /start")
            return

        problems = await get_user_problems(session, user.id, limit=10)

        if not problems:
            await message.answer("📭 У тебя пока нет решённых задач")
            return

        builder = InlineKeyboardBuilder()
        for p in problems:
            status_emoji = "✅" if p.status == "solved" else "⏳"
            title = p.title[:40] + "..." if len(p.title) > 40 else p.title
            builder.button(
                text=f"{status_emoji} {title}",
                callback_data=f"view_problem_{p.id}"
            )
        builder.adjust(1)

        await message.answer(
            "📖 **История решений:**",
            reply_markup=builder.as_markup()
        )


@router.message(F.text == "💳 Премиум")
async def menu_premium(message: Message):
    """Handle 'Premium' menu button"""
    text = """💳 **Пакеты решений**

Выбери подходящий пакет:

**🟢 Starter** — 5 решений
• Цена: 100 ⭐️ (~$2)
• Лимит вопросов в обсуждении: 10

**🔵 Medium** — 15 решений
• Цена: 250 ⭐️ (~$5)
• Лимит вопросов в обсуждении: 15

**🟣 Large** — 30 решений
• Цена: 500 ⭐️ (~$10)
• Лимит вопросов в обсуждении: 25

Решения не сгорают — используй когда удобно!"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Starter (100⭐️)", callback_data="buy_starter")
    builder.button(text="🔵 Medium (250⭐️)", callback_data="buy_medium")
    builder.button(text="🟣 Large (500⭐️)", callback_data="buy_large")
    builder.button(text="💬 Купить вопросы для обсуждения", callback_data="buy_discussions")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())


@router.message(F.text == "ℹ️ Помощь")
async def menu_help(message: Message):
    """Handle 'Help' menu button"""
    await cmd_help(message)
