from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user

router = Router()


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
    # Get or create user in database
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )

    # Create inline keyboard with main actions
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Решить проблему", callback_data="new_problem")
    builder.button(text="📖 История решений", callback_data="my_problems")
    builder.button(text="💳 Купить решения", callback_data="buy_solutions")
    builder.button(text="ℹ️ Помощь", callback_data="help")
    builder.adjust(1)  # 1 button per row

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

Готов разобраться? Жми "🚀 Решить проблему"!"""

    await message.answer(
        text=welcome_text,
        reply_markup=builder.as_markup()
    )

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

    await message.answer(help_text)

@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Handle help button press"""
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

    await callback.message.answer(help_text)
    await callback.answer()
