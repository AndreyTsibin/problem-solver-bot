"""Problem solving flow handlers with FSM"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.chat_action import ChatActionSender
import json
import random
import asyncio
from datetime import datetime

from bot.states import ProblemSolvingStates
from bot.services.claude_service import ClaudeService
from bot.services.prompt_builder import PromptBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id, create_problem, calculate_age
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

    # Create problem in DB and get user context
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        # Get user context
        age = calculate_age(user.birth_date) if user.birth_date else None

        user_context = {
            'gender': user.gender if user else None,
            'age': age,
            'occupation': user.occupation if user else None,
            'work_format': user.work_format if user else None
        }

        problem = await create_problem(
            session, user.id, problem_text,
            problem_type=None,  # Claude will determine internally
            methodology=None    # No fixed methodology
        )

        # Decrement problem credits
        user.problems_remaining -= 1
        remaining = user.problems_remaining
        await session.commit()

    # Save to state (including user context for all future requests)
    await state.update_data(
        problem_description=problem_text,
        conversation_history=[],
        current_step=1,
        problem_id=problem.id,
        user_context=user_context  # Save user context once at the beginning
    )

    # Ask first question immediately
    await state.set_state(ProblemSolvingStates.asking_questions)
    await ask_next_question(message, state)


async def ask_next_question(message: Message, state: FSMContext):
    """Generate and send next question with status message editing"""
    data = await state.get_data()
    user_context = data.get('user_context')  # Get user context from state

    # Show typing indicator while generating question
    bot = message.bot

    # Send status message that will be edited
    status_msg = await message.answer("⏳ Формулирую вопрос...")

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
            step=data['current_step'],
            user_context=user_context
        )

    # Edit status message to show the question
    await status_msg.edit_text(question)

    # Add to history
    history = data['conversation_history']
    history.append({"role": "assistant", "content": question})
    await state.update_data(conversation_history=history)


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
    if step > 4:
        await generate_final_solution(message, state)
    else:
        await ask_next_question(message, state)


async def generate_final_solution(message: Message, state: FSMContext):
    """Generate and show final solution with simple status message"""
    data = await state.get_data()
    await state.set_state(ProblemSolvingStates.generating_solution)

    bot = message.bot
    user_context = data.get('user_context')

    # Show status message
    status_msg = await message.answer("⏳ Анализирую всю информацию и готовлю решение...")

    # Keep typing indicator active
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Generate solution
    solution_text = await claude.generate_solution(
        problem_description=data['problem_description'],
        conversation_history=data['conversation_history'],
        user_context=user_context
    )

    # Save to DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Problem).where(Problem.id == data['problem_id'])
        )
        problem = result.scalar_one_or_none()

        if problem:
            problem.root_cause = solution_text[:500]
            problem.action_plan = solution_text
            problem.status = 'solved'
            problem.solved_at = datetime.utcnow()
            await session.commit()

    # Prepare discussion option
    await state.update_data(discussion_questions_used=0)

    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Продолжить обсуждение", callback_data="start_discussion")
    builder.adjust(1)

    # Delete status message and send solution
    try:
        await status_msg.delete()
    except Exception:
        pass

    await message.answer(solution_text, parse_mode="Markdown", reply_markup=builder.as_markup())


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
    data = await state.get_data()
    user_context = data.get('user_context')  # Get user context from state (saved at problem start)

    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        # Determine limits
        base_limits = {
            'starter': STARTER_DISCUSSION_LIMIT,
            'medium': MEDIUM_DISCUSSION_LIMIT,
            'large': LARGE_DISCUSSION_LIMIT
        }
        base_limit = base_limits.get(user.last_purchased_package, FREE_DISCUSSION_QUESTIONS)

        questions_used = data.get('discussion_questions_used', 0)
        total_available = base_limit + user.discussion_credits
        remaining = total_available - questions_used

        if remaining <= 0:
            builder = InlineKeyboardBuilder()
            builder.button(text="💬 Купить вопросы", callback_data="buy_discussions")
            builder.adjust(1)

            await message.answer(
                "❌ Лимит вопросов исчерпан!",
                reply_markup=builder.as_markup()
            )
            return

        # Generate answer using Claude with typing indicator
        conversation_history = data.get('conversation_history', [])
        user_question = message.text

        bot = message.bot

        # Send status message that will be edited
        status_msg = await message.answer("⏳ Обдумываю ответ...")

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
            answer = await claude.generate_discussion_answer(
                problem_description=data.get('problem_description', ''),
                conversation_history=conversation_history,
                user_question=user_question,
                user_context=user_context
            )

        # Add question and answer to history
        conversation_history.append({"role": "user", "content": user_question})
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

        # Edit status message to show the answer
        await status_msg.edit_text(f"💡 {answer}\n\n📊 Вопросов осталось: {remaining}/{total_available}")

        if remaining == 0:
            builder = InlineKeyboardBuilder()
            builder.button(text="💬 Купить вопросы", callback_data="buy_discussions")
            builder.adjust(1)

            await message.answer(
                "✅ Вопросы закончились!",
                reply_markup=builder.as_markup()
            )