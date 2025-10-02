"""Problem solving flow handlers with FSM"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.chat_action import ChatActionSender
import json
import random
from datetime import datetime

from bot.states import ProblemSolvingStates
from bot.services.claude_service import ClaudeService
from bot.services.prompt_builder import PromptBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id, create_problem
from bot.database.models import Problem
from bot.config import (
    FREE_DISCUSSION_QUESTIONS,
    STARTER_DISCUSSION_LIMIT,
    MEDIUM_DISCUSSION_LIMIT,
    LARGE_DISCUSSION_LIMIT
)
from sqlalchemy import select

router = Router()
claude = ClaudeService()
prompt_builder = PromptBuilder()


def get_random_thinking_message(context: str) -> str:
    """Get random thinking message based on context"""
    messages = {
        "question": [
            "Хм, интересно... 🤔",
            "Дай подумаю...",
            "Сейчас сформулирую вопрос...",
            "Минутку...",
            "Понял, идём дальше..."
        ],
        "solution": [
            "Сейчас всё проанализирую... 🔍",
            "Минутку, формулирую решение...",
            "Собираю всё воедино...",
            "Анализирую информацию..."
        ],
        "discussion": [
            "Хороший вопрос! 🤔",
            "Дай подумаю...",
            "Сейчас отвечу...",
            "Минутку..."
        ]
    }
    return random.choice(messages.get(context, ["Думаю..."]))


@router.callback_query(F.data == "new_problem")
async def start_new_problem(callback: CallbackQuery, state: FSMContext):
    """Handle 'New Problem' button"""
    # Check user limits
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)

        if user.problems_remaining <= 0:
            builder = InlineKeyboardBuilder()
            builder.button(text="💳 Купить решения", callback_data="buy_solutions")
            builder.adjust(1)

            await callback.message.answer(
                "❌ У тебя закончились решения!\n\n"
                "💳 Купи пакет решений, чтобы продолжить анализ проблем.",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
            return

    await callback.message.answer(
        "🎯 Опиши свою проблему своими словами.\n\n"
        "Расскажи что происходит — коротко или подробно, как тебе удобно."
    )
    await state.set_state(ProblemSolvingStates.waiting_for_problem)
    await callback.answer()


@router.message(ProblemSolvingStates.waiting_for_problem)
async def receive_problem(message: Message, state: FSMContext):
    """Start problem analysis (simplified - no pre-analysis)"""
    problem_text = message.text

    # Save to state (no methodology analysis needed)
    await state.update_data(
        problem_description=problem_text,
        conversation_history=[],
        current_step=1
    )

    # Create problem in DB
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        problem = await create_problem(
            session, user.id, problem_text,
            problem_type=None,  # Claude will determine internally
            methodology=None    # No fixed methodology
        )
        await state.update_data(problem_id=problem.id)

        # Decrement problem credits
        user.problems_remaining -= 1
        remaining = user.problems_remaining
        await session.commit()

    # Ask first question immediately
    await state.set_state(ProblemSolvingStates.asking_questions)
    await ask_next_question(message, state)


async def ask_next_question(message: Message, state: FSMContext):
    """Generate and send next question"""
    data = await state.get_data()

    # Show typing indicator while generating question
    bot = message.bot

    # Send processing message
    processing_msg = await message.answer(get_random_thinking_message("question"))

    # Send initial typing indicator immediately
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Keep typing indicator active during Claude request
    async with ChatActionSender(
        bot=bot,
        chat_id=message.chat.id,
        action="typing",
        initial_sleep=0.5,
        interval=3.0
    ):
        question = await claude.generate_question(
            problem_description=data['problem_description'],
            conversation_history=data['conversation_history'],
            step=data['current_step']
        )

    # Delete processing message
    await processing_msg.delete()

    # Add to history
    history = data['conversation_history']
    history.append({"role": "assistant", "content": question})
    await state.update_data(conversation_history=history)

    # Send with skip button only
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Пропустить вопрос", callback_data="skip_question")
    builder.adjust(1)

    await message.answer(
        question,
        reply_markup=builder.as_markup()
    )


@router.message(ProblemSolvingStates.asking_questions)
async def receive_answer(message: Message, state: FSMContext):
    """Process user's answer"""
    data = await state.get_data()

    # Add answer to history
    history = data['conversation_history']
    history.append({"role": "user", "content": message.text})

    step = data['current_step'] + 1
    await state.update_data(
        conversation_history=history,
        current_step=step
    )

    # Check if done
    if step > 5:
        await generate_final_solution(message, state)
    else:
        await ask_next_question(message, state)


@router.callback_query(F.data == "get_solution")
async def handle_get_solution(callback: CallbackQuery, state: FSMContext):
    """User wants solution now"""
    await generate_final_solution(callback.message, state)
    await callback.answer()


async def generate_final_solution(message: Message, state: FSMContext):
    """Generate and show final solution"""
    data = await state.get_data()

    await state.set_state(ProblemSolvingStates.generating_solution)

    # Show typing indicator while generating solution
    bot = message.bot

    # Send processing message
    processing_msg = await message.answer(get_random_thinking_message("solution"))

    # Send initial typing indicator immediately
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Keep typing indicator active during Claude request
    async with ChatActionSender(
        bot=bot,
        chat_id=message.chat.id,
        action="typing",
        initial_sleep=0.5,
        interval=3.0
    ):
        solution_text = await claude.generate_solution(
            problem_description=data['problem_description'],
            conversation_history=data['conversation_history']
        )

    # Delete processing message
    await processing_msg.delete()

    # Save to DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Problem).where(Problem.id == data['problem_id'])
        )
        problem = result.scalar_one_or_none()

        if problem:
            problem.root_cause = solution_text[:500]  # Store first 500 chars
            problem.action_plan = solution_text  # Store full solution
            problem.status = 'solved'
            problem.solved_at = datetime.utcnow()
            await session.commit()

    # Offer discussion option
    await state.update_data(discussion_questions_used=0)

    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Продолжить обсуждение", callback_data="start_discussion")
    builder.adjust(1)

    # Send solution with Markdown formatting and discussion button
    await message.answer(solution_text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data == "skip_question")
async def skip_question(callback: CallbackQuery, state: FSMContext):
    """Skip current question"""
    data = await state.get_data()
    step = data['current_step'] + 1
    await state.update_data(current_step=step)

    if step > 5:
        await generate_final_solution(callback.message, state)
    else:
        await ask_next_question(callback.message, state)

    await callback.answer("Пропущено")


# Discussion system handlers
@router.callback_query(F.data == "start_discussion")
async def start_discussion(callback: CallbackQuery, state: FSMContext):
    """Start discussion mode after solution"""
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)

        # Determine base discussion limit from last package
        base_limits = {
            'starter': STARTER_DISCUSSION_LIMIT,
            'medium': MEDIUM_DISCUSSION_LIMIT,
            'large': LARGE_DISCUSSION_LIMIT
        }
        base_limit = base_limits.get(user.last_purchased_package, FREE_DISCUSSION_QUESTIONS)

        data = await state.get_data()
        questions_used = data.get('discussion_questions_used', 0)
        total_available = base_limit + user.discussion_credits
        remaining = total_available - questions_used

        if remaining <= 0:
            builder = InlineKeyboardBuilder()
            builder.button(text="💬 Купить вопросы", callback_data="buy_discussions")
            builder.adjust(1)

            from bot.keyboards import get_main_menu_keyboard
            await callback.message.answer(
                "❌ Вопросы для обсуждения закончились!\n\n"
                f"📊 Базовый лимит: {base_limit}\n"
                f"💬 Дополнительные: {user.discussion_credits}\n"
                f"✅ Использовано: {questions_used}\n\n"
                "Купи дополнительные вопросы или используй меню для навигации 👇",
                reply_markup=builder.as_markup()
            )
            await callback.message.answer("Меню:", reply_markup=get_main_menu_keyboard())
            await callback.answer()
            return

        await state.set_state(ProblemSolvingStates.discussing_solution)
        await callback.message.answer(
            f"💬 **Обсуждение решения**\n\n"
            f"Вопросов осталось: {remaining}/{total_available}\n\n"
            f"Задай любой вопрос по решению проблемы."
        )
        await callback.answer()


@router.message(ProblemSolvingStates.discussing_solution)
async def handle_discussion_question(message: Message, state: FSMContext):
    """Handle user's discussion question"""
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        # Determine limits
        base_limits = {
            'starter': STARTER_DISCUSSION_LIMIT,
            'medium': MEDIUM_DISCUSSION_LIMIT,
            'large': LARGE_DISCUSSION_LIMIT
        }
        base_limit = base_limits.get(user.last_purchased_package, FREE_DISCUSSION_QUESTIONS)

        data = await state.get_data()
        questions_used = data.get('discussion_questions_used', 0)
        total_available = base_limit + user.discussion_credits
        remaining = total_available - questions_used

        if remaining <= 0:
            builder = InlineKeyboardBuilder()
            builder.button(text="💬 Купить вопросы", callback_data="buy_discussions")
            builder.adjust(1)

            from bot.keyboards import get_main_menu_keyboard
            await message.answer(
                "❌ Лимит вопросов исчерпан!",
                reply_markup=builder.as_markup()
            )
            await message.answer("Меню:", reply_markup=get_main_menu_keyboard())
            return

        # Generate answer using Claude with typing indicator
        conversation_history = data.get('conversation_history', [])
        conversation_history.append({"role": "user", "content": message.text})

        bot = message.bot

        # Send processing message
        processing_msg = await message.answer(get_random_thinking_message("discussion"))

        # Send initial typing indicator immediately
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # Keep typing indicator active during Claude request
        async with ChatActionSender(
            bot=bot,
            chat_id=message.chat.id,
            action="typing",
            initial_sleep=0.5,
            interval=3.0
        ):
            answer = await claude.generate_question(
                problem_description=data.get('problem_description', ''),
                conversation_history=conversation_history,
                step=questions_used + 1
            )

        # Delete processing message
        await processing_msg.delete()

        conversation_history.append({"role": "assistant", "content": answer})

        # Increment counter and deduct from appropriate pool
        questions_used += 1
        if questions_used > base_limit:
            # Deduct from purchased credits
            credits_used_from_purchased = questions_used - base_limit
            user.discussion_credits = max(0, user.discussion_credits - 1)
            await session.commit()

        await state.update_data(
            discussion_questions_used=questions_used,
            conversation_history=conversation_history
        )

        remaining = total_available - questions_used

        await message.answer(f"💡 {answer}\n\n📊 Вопросов осталось: {remaining}/{total_available}")

        if remaining == 0:
            builder = InlineKeyboardBuilder()
            builder.button(text="💬 Купить вопросы", callback_data="buy_discussions")
            builder.adjust(1)

            from bot.keyboards import get_main_menu_keyboard
            await message.answer(
                "✅ Вопросы закончились!",
                reply_markup=builder.as_markup()
            )
            await message.answer("Меню:", reply_markup=get_main_menu_keyboard())