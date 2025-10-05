from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user, calculate_age
from bot.keyboards import get_main_menu_keyboard
from bot.states import OnboardingStates, ProblemSolvingStates
import structlog
import asyncio
from datetime import datetime, timedelta
from typing import Tuple, Union

router = Router()
logger = structlog.get_logger(__name__)

# Track last /start call per user to prevent duplicates
_last_start_calls = {}
_THROTTLE_SECONDS = 2


def validate_birth_date(text: str) -> Tuple[bool, Union[datetime, str]]:
    """Validate birth date format and value"""
    try:
        # Parse DD.MM.YYYY
        birth_date = datetime.strptime(text.strip(), "%d.%m.%Y")

        # Check not in future
        if birth_date > datetime.now():
            return False, "Дата не может быть в будущем 🤔"

        # Check age range (14-100 years)
        age = calculate_age(birth_date)
        if age < 14:
            return False, "Тебе должно быть минимум 14 лет для использования бота"
        if age > 100:
            return False, "Пожалуйста, укажи корректную дату рождения"

        return True, birth_date

    except ValueError:
        return False, "Неверный формат ⚠️\n\nИспользуй формат ДД.ММ.ГГГГ\nНапример: 15.03.1995"




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
        "🎯 Опиши свою проблему своими словами:\n\n"
        "📝 Укажи:\n"
        "• Что именно происходит?\n"
        "• Как долго это длится?\n"
        "• Что уже пробовал(а)?\n\n"
        "💡 Чем подробнее опишешь — тем точнее решение!"
    )
    await state.set_state(ProblemSolvingStates.waiting_for_problem)


# Old menu handlers removed - functionality moved to profile.py


# Gender selection handlers
@router.callback_query(F.data == "gender_male")
async def handle_gender_male(callback: CallbackQuery, state: FSMContext):
    """Handle male gender selection"""
    from bot.states import OnboardingStates

    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id

        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.gender = 'male'
            await session.commit()
            logger.info(f"User {user.telegram_id} selected gender: male")

    # Move to birth date input
    await state.set_state(OnboardingStates.entering_birth_date)

    await callback.message.edit_text(
        "📅 Укажи дату рождения (ДД.ММ.ГГГГ)\n\n"
        "Например: 15.03.1995\n\n"
        "Возраст важен для точности — решения для 20 и 40 лет сильно отличаются.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "gender_female")
async def handle_gender_female(callback: CallbackQuery, state: FSMContext):
    """Handle female gender selection"""
    from bot.states import OnboardingStates

    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id

        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.gender = 'female'
            await session.commit()
            logger.info(f"User {user.telegram_id} selected gender: female")

    # Move to birth date input
    await state.set_state(OnboardingStates.entering_birth_date)

    await callback.message.edit_text(
        "📅 Укажи дату рождения (ДД.ММ.ГГГГ)\n\n"
        "Например: 15.03.1995\n\n"
        "Возраст важен для точности — решения для 20 и 40 лет сильно отличаются.",
        parse_mode="HTML"
    )
    await callback.answer()

# New onboarding handlers
@router.message(OnboardingStates.entering_birth_date)
async def handle_birth_date_input(message: Message, state: FSMContext):
    """Handle birth date input"""
    from bot.states import OnboardingStates

    # Validate birth date
    is_valid, result = validate_birth_date(message.text)

    if not is_valid:
        # Send error message
        await message.answer(result)
        return

    # Save birth date to database
    birth_date = result
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id

        user = await get_user_by_telegram_id(session, message.from_user.id)
        if user:
            user.birth_date = birth_date
            await session.commit()
            logger.info(f"User {user.telegram_id} entered birth date: {birth_date}")

    # Move to occupation input
    await state.set_state(OnboardingStates.entering_occupation)

    await message.answer(
        "💼 Чем занимаешься?\n\n"
        "Напиши кратко (1-3 слова):\n"
        "• Менеджер в IT\n"
        "• Студент МГУ\n"
        "• Свой бизнес (кафе)\n"
        "• Не работаю\n"
        "• и т.д."
    )


@router.message(OnboardingStates.entering_occupation)
async def handle_occupation_input(message: Message, state: FSMContext):
    """Handle occupation input"""
    from bot.states import OnboardingStates

    occupation = message.text.strip()

    # Basic validation
    if len(occupation) < 2:
        await message.answer("Слишком короткий ответ. Напиши хотя бы 2 символа.")
        return

    if len(occupation) > 100:
        await message.answer("Слишком длинный ответ. Укажи кратко (до 100 символов).")
        return

    # Save occupation to database
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id

        user = await get_user_by_telegram_id(session, message.from_user.id)
        if user:
            user.occupation = occupation
            await session.commit()
            logger.info(f"User {user.telegram_id} entered occupation: {occupation}")

    # Move to work format selection
    await state.set_state(OnboardingStates.choosing_work_format)

    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Дома (удаленно)", callback_data="work_format_remote")
    builder.button(text="🏢 В офисе", callback_data="work_format_office")
    builder.button(text="🔀 Гибрид (дом + офис)", callback_data="work_format_hybrid")
    builder.button(text="🎓 Учусь / не работаю", callback_data="work_format_student")
    builder.adjust(1)

    await message.answer(
        "🏠 Где работаешь?",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("work_format_"))
async def handle_work_format_selection(callback: CallbackQuery, state: FSMContext):
    """Handle work format selection"""
    from bot.database.crud_subscriptions import get_user_by_referral_code, create_referral

    work_format = callback.data.replace("work_format_", "")

    # Save work format to database
    async with AsyncSessionLocal() as session:
        from bot.database.crud import get_user_by_telegram_id

        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.work_format = work_format
            await session.commit()
            logger.info(f"User {user.telegram_id} selected work format: {work_format}")

        # Process referral if stored in state
        data = await state.get_data()
        referral_code = data.get('referral_code')
        referral_bonus_message = ""

        if referral_code and user:
            try:
                referrer = await get_user_by_referral_code(session, referral_code)
                if referrer and referrer.id != user.id:
                    # Create referral record and grant rewards
                    await create_referral(session, referrer.id, user.id)
                    gender_word = "получил" if user.gender == "male" else "получила"
                    referral_bonus_message = f"\n\n✨ <b>Бонус!</b> Ты {gender_word} +1 решение от друга!\n"

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

    # Clear onboarding state
    await state.clear()

    # Send welcome message
    welcome_text = f"""✅ Отлично! Профиль создан.

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
        parse_mode="HTML"
    )
    await callback.message.answer(
        "👇",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
