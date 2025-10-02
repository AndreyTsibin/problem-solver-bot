"""Problem solving flow handlers with FSM"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
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
        "🎯 Опиши свою проблему в 2-3 предложениях.\n\n"
        "Что происходит и почему это важно решить?"
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

    await message.answer(
        f"✅ Принял! Задам несколько вопросов для глубокого анализа.\n\n"
        f"💳 Решений осталось: {remaining}"
    )

    # Ask first question
    await state.set_state(ProblemSolvingStates.asking_questions)
    await ask_next_question(message, state)


async def ask_next_question(message: Message, state: FSMContext):
    """Generate and send next question"""
    data = await state.get_data()

    # Show thinking indicator
    await message.answer("🤔 Думаю над вопросом...")

    question = await claude.generate_question(
        problem_description=data['problem_description'],
        conversation_history=data['conversation_history'],
        step=data['current_step']
    )

    # Add to history
    history = data['conversation_history']
    history.append({"role": "assistant", "content": question})
    await state.update_data(conversation_history=history)

    # Send with keyboard
    builder = InlineKeyboardBuilder()
    if data['current_step'] >= 3:
        builder.button(text="✅ Хватит, дай решение", callback_data="get_solution")
    builder.button(text="⏭️ Пропустить вопрос", callback_data="skip_question")
    builder.adjust(1)

    await message.answer(
        f"❓ Вопрос {data['current_step']}/5:\n\n{question}",
        reply_markup=builder.as_markup()
    )


@router.message(ProblemSolvingStates.asking_questions)
async def receive_answer(message: Message, state: FSMContext):
    """Process user's answer"""
    # Show thinking indicator immediately
    await message.answer("🤔 Принял, думаю над следующим вопросом...")

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

    # Show thinking indicator
    await message.answer("🎯 Генерирую решение...")

    solution_text = await claude.generate_solution(
        problem_description=data['problem_description'],
        conversation_history=data['conversation_history']
    )

    # Send solution (it's already formatted with emojis)
    await message.answer(solution_text, parse_mode=None)

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
    data = await state.get_data()
    await state.update_data(discussion_questions_used=0)

    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Продолжить обсуждение", callback_data="start_discussion")
    builder.button(text="🚀 Решить новую проблему", callback_data="new_problem")
    builder.button(text="📖 История решений", callback_data="my_problems")
    builder.adjust(1)

    await message.answer("Что дальше?", reply_markup=builder.as_markup())


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
            builder.button(text="🚀 Начать новую сессию", callback_data="new_problem")
            builder.adjust(1)

            await callback.message.answer(
                "❌ Вопросы для обсуждения закончились!\n\n"
                f"📊 Базовый лимит: {base_limit}\n"
                f"💬 Дополнительные: {user.discussion_credits}\n"
                f"✅ Использовано: {questions_used}\n\n"
                "Купи дополнительные вопросы или начни новую сессию.",
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
            builder.button(text="🚀 Начать новую сессию", callback_data="new_problem")
            builder.adjust(1)

            await message.answer(
                "❌ Лимит вопросов исчерпан!",
                reply_markup=builder.as_markup()
            )
            return

        # Generate answer using Claude
        await message.answer("🤔 Думаю над ответом...")

        conversation_history = data.get('conversation_history', [])
        conversation_history.append({"role": "user", "content": message.text})

        answer = await claude.generate_question(
            problem_description=data.get('problem_description', ''),
            conversation_history=conversation_history,
            step=questions_used + 1
        )

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
            builder.button(text="🚀 Начать новую сессию", callback_data="new_problem")
            builder.adjust(1)

            await message.answer(
                "✅ Вопросы закончились!",
                reply_markup=builder.as_markup()
            )