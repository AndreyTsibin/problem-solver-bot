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
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command with optional referral code"""
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

    # Parse referral code from deep link (e.g., /start ref_ABC12345)
    referral_code = None
    if message.text and len(message.text.split()) > 1:
        param = message.text.split()[1]
        if param.startswith("ref_"):
            referral_code = param[4:]  # Remove "ref_" prefix
            logger.info(f"Detected referral code: {referral_code}")

    # Get or create user in database
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id
        from bot.database.crud_subscriptions import get_user_by_referral_code, create_referral

        # Check if user is new
        existing_user = await get_user_by_telegram_id(session, message.from_user.id)
        is_new_user = existing_user is None

        user = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )

        # Check if user has gender set
        if not user.gender:
            # Store referral code in state for later use
            if referral_code:
                await state.update_data(referral_code=referral_code)

            # Ask for gender first
            from bot.states import OnboardingStates
            await state.set_state(OnboardingStates.choosing_gender)

            gender_text = f"""👋 Привет, {message.from_user.first_name}!

Я твой коуч по решению проблем.

⚡ <b>Чтобы дать максимально точное решение, мне важно знать твой пол.</b>

<b>Почему это важно?</b>
Мужчины и женщины по-разному подходят к проблемам:
• Разный фокус вопросов
• Разные триггеры и решения
• Разный стиль анализа

Это напрямую влияет на качество решения!

Выбери свой пол:"""

            builder = InlineKeyboardBuilder()
            builder.button(text="👨 Я парень", callback_data="gender_male")
            builder.button(text="👩 Я девушка", callback_data="gender_female")
            builder.adjust(2)

            await message.answer(
                text=gender_text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            logger.info(f"Requesting gender from new user {message.from_user.id}")
            return

        # Process referral if user is new and code is valid
        referral_bonus_message = ""
        if is_new_user and referral_code:
            try:
                referrer = await get_user_by_referral_code(session, referral_code)
                if referrer and referrer.id != user.id:
                    # Create referral record and grant rewards
                    await create_referral(session, referrer.id, user.id)
                    referral_bonus_message = "\n\n✨ <b>Бонус!</b> Ты получил +1 решение от друга!\n"

                    # Notify referrer
                    try:
                        await message.bot.send_message(
                            referrer.telegram_id,
                            "🎉 <b>Твой друг присоединился!</b>\n\n"
                            "Ты получил +1 бонусное решение за приглашение.",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to notify referrer {referrer.telegram_id}: {e}")

                    logger.info(f"Referral processed: {referrer.id} -> {user.id}")
                else:
                    logger.info(f"Invalid referral: code={referral_code}, referrer={referrer}")
            except Exception as e:
                logger.error(f"Error processing referral: {e}")

    # Welcome message
    welcome_text = f"""👋 Привет, {message.from_user.first_name}!

Я твой личный коуч по решению проблем. Помогу разобраться в любой ситуации и найти реальное решение.

💬 <b>Что я умею:</b>
• Задаю правильные вопросы, которые помогают увидеть суть
• Нахожу корневую причину, а не просто симптомы
• Даю конкретный план действий с дедлайнами

⚡ <b>Как работаем:</b>
1. Ты описываешь проблему своими словами
2. Я задаю 3-5 уточняющих вопросов
3. Ты получаешь решение с конкретными шагами{referral_bonus_message}

Используй меню внизу для навигации! 👇"""

    logger.info(f"Sending welcome message to user {message.from_user.id}")
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    logger.info(f"Welcome message sent to user {message.from_user.id}")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """📚 **Как работать с ботом:**

1️⃣ Нажми "🚀 Решить проблему"
2️⃣ Опиши проблему своими словами
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
2️⃣ Опиши проблему своими словами
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
        "🎯 Опиши свою проблему своими словами.\n\n"
        "Расскажи что происходит — коротко или подробно, как тебе удобно."
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
    text = """💎 <b>Подписки и пакеты</b>

<b>📅 Ежемесячные подписки:</b>

<b>🟢 Стандарт</b> — 599₽/мес
• 15 решений каждый месяц
• 15 вопросов в обсуждении
• История за 3 месяца

<b>🟣 Премиум</b> — 999₽/мес
• 30 решений каждый месяц
• 25 вопросов в обсуждении
• Полная история
• Приоритетная обработка

━━━━━━━━━━━━━━━━━━━━

<b>💰 Разовые пакеты:</b>

<b>🟢 Starter</b> — 250₽
• 5 решений
• 10 вопросов в обсуждении

<b>🔵 Medium</b> — 600₽
• 15 решений
• 15 вопросов в обсуждении

<b>🟣 Large</b> — 1200₽
• 30 решений
• 25 вопросов в обсуждении

💡 Решения не сгорают — используй когда удобно!"""

    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Оформить подписку", callback_data="show_subscriptions")
    builder.button(text="🟢 Starter (250₽)", callback_data="buy_starter")
    builder.button(text="🔵 Medium (600₽)", callback_data="buy_medium")
    builder.button(text="🟣 Large (1200₽)", callback_data="buy_large")
    builder.button(text="💬 Купить вопросы", callback_data="buy_discussions")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.message(F.text == "ℹ️ Помощь")
async def menu_help(message: Message):
    """Handle 'Help' menu button"""
    await cmd_help(message)


@router.callback_query(F.data == "show_subscriptions")
async def callback_show_subscriptions(callback: CallbackQuery):
    """Show subscription options"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    text = """💎 <b>Ежемесячные подписки</b>

<b>🟢 Стандарт</b> — 599₽/мес
• 15 решений каждый месяц
• 15 вопросов в обсуждении
• История за 3 месяца
• Автопродление

<b>🟣 Премиум</b> — 999₽/мес
• 30 решений каждый месяц
• 25 вопросов в обсуждении
• Полная история
• Приоритетная обработка
• Автопродление

Решения обновляются автоматически каждый месяц!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🟢 Стандарт (599₽)",
            callback_data="subscribe_standard"
        )],
        [InlineKeyboardButton(
            text="🟣 Премиум (999₽)",
            callback_data="subscribe_premium"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_premium"
        )]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_to_premium")
async def callback_back_to_premium(callback: CallbackQuery):
    """Go back to premium menu"""
    await menu_premium(callback.message)
    await callback.answer()


@router.message(F.text == "💎 Подписки")
async def menu_subscriptions(message: Message):
    """Handle 'Subscriptions' menu button - redirect to /subscription command"""
    from bot.handlers.subscription import handle_subscription_command
    await handle_subscription_command(message)


@router.message(F.text == "🎁 Рефералы")
async def menu_referrals(message: Message):
    """Handle 'Referrals' menu button - redirect to /referral command"""
    from bot.handlers.referral import handle_referral_command
    await handle_referral_command(message)


# Gender selection handlers
@router.callback_query(F.data == "gender_male")
async def handle_gender_male(callback: CallbackQuery, state: FSMContext):
    """Handle male gender selection"""
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id
        from bot.database.crud_subscriptions import get_user_by_referral_code, create_referral

        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.gender = 'male'
            await session.commit()
            logger.info(f"User {user.telegram_id} selected gender: male")

            # Process referral if stored in state
            data = await state.get_data()
            referral_code = data.get('referral_code')
            referral_bonus_message = ""

            if referral_code:
                try:
                    referrer = await get_user_by_referral_code(session, referral_code)
                    if referrer and referrer.id != user.id:
                        # Create referral record and grant rewards
                        await create_referral(session, referrer.id, user.id)
                        referral_bonus_message = "\n\n✨ <b>Бонус!</b> Ты получил +1 решение от друга!\n"

                        # Notify referrer
                        try:
                            await callback.bot.send_message(
                                referrer.telegram_id,
                                "🎉 <b>Твой друг присоединился!</b>\n\n"
                                "Ты получил +1 бонусное решение за приглашение.",
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to notify referrer {referrer.telegram_id}: {e}")

                        logger.info(f"Referral processed: {referrer.id} -> {user.id}")
                except Exception as e:
                    logger.error(f"Error processing referral: {e}")

    # Clear state
    await state.clear()

    # Send welcome message
    welcome_text = f"""👋 Отлично!

Я твой личный коуч по решению проблем. Помогу разобраться в любой ситуации и найти реальное решение.

💬 <b>Что я умею:</b>
• Задаю правильные вопросы, которые помогают увидеть суть
• Нахожу корневую причину, а не просто симптомы
• Даю конкретный план действий с дедлайнами

⚡ <b>Как работаем:</b>
1. Ты описываешь проблему своими словами
2. Я задаю 3-5 уточняющих вопросов
3. Ты получаешь решение с конкретными шагами{referral_bonus_message}

Используй меню внизу для навигации! 👇"""

    await callback.message.edit_text(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "gender_female")
async def handle_gender_female(callback: CallbackQuery, state: FSMContext):
    """Handle female gender selection"""
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id
        from bot.database.crud_subscriptions import get_user_by_referral_code, create_referral

        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.gender = 'female'
            await session.commit()
            logger.info(f"User {user.telegram_id} selected gender: female")

            # Process referral if stored in state
            data = await state.get_data()
            referral_code = data.get('referral_code')
            referral_bonus_message = ""

            if referral_code:
                try:
                    referrer = await get_user_by_referral_code(session, referral_code)
                    if referrer and referrer.id != user.id:
                        # Create referral record and grant rewards
                        await create_referral(session, referrer.id, user.id)
                        referral_bonus_message = "\n\n✨ <b>Бонус!</b> Ты получила +1 решение от друга!\n"

                        # Notify referrer
                        try:
                            await callback.bot.send_message(
                                referrer.telegram_id,
                                "🎉 <b>Твой друг присоединился!</b>\n\n"
                                "Ты получил +1 бонусное решение за приглашение.",
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to notify referrer {referrer.telegram_id}: {e}")

                        logger.info(f"Referral processed: {referrer.id} -> {user.id}")
                except Exception as e:
                    logger.error(f"Error processing referral: {e}")

    # Clear state
    await state.clear()

    # Send welcome message
    welcome_text = f"""👋 Отлично!

Я твой личный коуч по решению проблем. Помогу разобраться в любой ситуации и найти реальное решение.

💬 <b>Что я умею:</b>
• Задаю правильные вопросы, которые помогают увидеть суть
• Нахожу корневую причину, а не просто симптомы
• Даю конкретный план действий с дедлайнами

⚡ <b>Как работаем:</b>
1. Ты описываешь проблему своими словами
2. Я задаю 3-5 уточняющих вопросов
3. Ты получаешь решение с конкретными шагами{referral_bonus_message}

Используй меню внизу для навигации! 👇"""

    await callback.message.edit_text(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
