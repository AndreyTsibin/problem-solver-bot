from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user

router = Router()

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

Я помогу тебе систематически разобрать любую проблему и найти решение.

🎯 **Как это работает:**
1. Опиши свою проблему
2. Я задам уточняющие вопросы
3. Ты получишь корневую причину и план действий

📊 **Используемые методики:**
• 5 Почему — для линейных проблем
• Fishbone — для многофакторных ситуаций
• First Principles — для системных вызовов

💳 **Доступно решений:** {user.problems_remaining}
💬 **Доступно вопросов:** {user.discussion_credits}

Готов начать?"""

    await message.answer(
        text=welcome_text,
        reply_markup=builder.as_markup()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """📚 **Как пользоваться ботом:**

1️⃣ Нажми "🚀 Решить проблему"
2️⃣ Опиши проблему в 2-3 предложениях
3️⃣ Отвечай на мои уточняющие вопросы
4️⃣ Получи детальный план решения

🔍 **Типы проблем:**

**Линейная** — прямая причина-следствие
Пример: "Не могу встать рано утром"
→ Использую методику "5 Почему"

**Многофакторная** — несколько причин
Пример: "Падают продажи в магазине"
→ Использую методику "Fishbone"

**Системная** — сложные взаимосвязи
Пример: "Как выйти на новый рынок"
→ Использую методику "First Principles"

💡 **Советы:**
• Будь конкретным в описании
• Отвечай честно на вопросы
• Не спеши — качество важнее скорости

❓ **Вопросы?** Пиши @your_username"""

    await message.answer(help_text)

@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Handle help button press"""
    help_text = """📚 **Как пользоваться ботом:**

1️⃣ Нажми "🚀 Решить проблему"
2️⃣ Опиши проблему в 2-3 предложениях
3️⃣ Отвечай на мои уточняющие вопросы
4️⃣ Получи детальный план решения

🔍 **Типы проблем:**

**Линейная** — прямая причина-следствие
Пример: "Не могу встать рано утром"
→ Использую методику "5 Почему"

**Многофакторная** — несколько причин
Пример: "Падают продажи в магазине"
→ Использую методику "Fishbone"

**Системная** — сложные взаимосвязи
Пример: "Как выйти на новый рынок"
→ Использую методику "First Principles"

💡 **Советы:**
• Будь конкретным в описании
• Отвечай честно на вопросы
• Не спеши — качество важнее скорости

❓ **Вопросы?** Пиши @your_username"""

    await callback.message.answer(help_text)
    await callback.answer()
