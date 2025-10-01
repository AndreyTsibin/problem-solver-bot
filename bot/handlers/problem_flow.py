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

        if not user.is_premium and user.free_problems_left <= 0:
            await callback.message.answer(
                "❌ Бесплатный лимит исчерпан!\n\n"
                "Нажми 💎 Премиум чтобы продолжить"
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
    """Analyze problem type"""
    problem_text = message.text

    await message.answer("🔍 Анализирую проблему...")

    # Analyze with Claude
    analysis = await claude.analyze_problem_type(problem_text)

    # Save to state
    await state.update_data(
        problem_description=problem_text,
        problem_type=analysis['type'],
        methodology=analysis['methodology'],
        conversation_history=[],
        current_step=1
    )

    # Create problem in DB
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        problem = await create_problem(
            session, user.id, problem_text,
            analysis['type'], analysis['methodology']
        )
        await state.update_data(problem_id=problem.id)

        # Decrement free problems
        if not user.is_premium:
            user.free_problems_left -= 1
            await session.commit()

    methodology_names = {
        '5_whys': '5 Почему',
        'fishbone': 'Fishbone',
        'first_principles': 'First Principles'
    }

    await message.answer(
        f"✅ Тип проблемы: **{analysis['type']}**\n"
        f"📊 Методика: **{methodology_names.get(analysis['methodology'], analysis['methodology'])}**\n\n"
        f"Задам несколько вопросов для глубокого анализа 👇"
    )

    # Ask first question
    await state.set_state(ProblemSolvingStates.asking_questions)
    await ask_next_question(message, state)


async def ask_next_question(message: Message, state: FSMContext):
    """Generate and send next question"""
    data = await state.get_data()

    question = await claude.generate_question(
        methodology=data['methodology'],
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
    await callback.message.answer("🎯 Генерирую решение...")
    await generate_final_solution(callback.message, state)
    await callback.answer()


async def generate_final_solution(message: Message, state: FSMContext):
    """Generate and show final solution"""
    data = await state.get_data()

    await state.set_state(ProblemSolvingStates.generating_solution)

    solution = await claude.generate_solution(
        problem_description=data['problem_description'],
        methodology=data['methodology'],
        conversation_history=data['conversation_history']
    )

    # Format solution message
    solution_text = f"""🎯 **КОРНЕВАЯ ПРИЧИНА:**
{solution['root_cause']}

📊 **АНАЛИЗ:**
• Методика: {solution['analysis']['methodology']}
• Факторы: {', '.join(solution['analysis']['key_factors'][:3])}

📋 **ПЛАН ДЕЙСТВИЙ:**

**Сейчас (24ч):**
{chr(10).join(['□ ' + a for a in solution['action_plan']['immediate']])}

**Эта неделя:**
{chr(10).join(['□ ' + a for a in solution['action_plan']['this_week']])}

**Долгосрочно:**
{chr(10).join(['□ ' + a for a in solution['action_plan']['long_term']])}

📈 **МЕТРИКИ:**
{chr(10).join([f"• {m['what']} → {m['target']}" for m in solution['metrics']])}"""

    await message.answer(solution_text)

    # Save to DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Problem).where(Problem.id == data['problem_id'])
        )
        problem = result.scalar_one_or_none()

        if problem:
            problem.root_cause = solution['root_cause']
            problem.action_plan = json.dumps(solution['action_plan'], ensure_ascii=False)
            problem.status = 'solved'
            problem.solved_at = datetime.utcnow()
            await session.commit()

    # Back to menu
    builder = InlineKeyboardBuilder()
    builder.button(text="🆕 Новая проблема", callback_data="new_problem")
    builder.button(text="📋 Мои проблемы", callback_data="my_problems")
    builder.adjust(1)

    await message.answer("Что дальше?", reply_markup=builder.as_markup())
    await state.clear()


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