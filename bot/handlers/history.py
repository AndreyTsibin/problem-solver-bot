from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id, get_user_problems

router = Router()

@router.callback_query(F.data == "my_problems")
async def show_problems_list(callback: CallbackQuery):
    """Show user's problems history"""
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        problems = await get_user_problems(session, user.id, limit=10)

        if not problems:
            await callback.message.answer("📭 У тебя пока нет решённых проблем")
            await callback.answer()
            return

        builder = InlineKeyboardBuilder()
        for p in problems:
            status_emoji = "✅" if p.status == "solved" else "⏳"
            title = p.title[:40] + "..." if len(p.title) > 40 else p.title
            builder.button(
                text=f"{status_emoji} {title}",
                callback_data=f"view_problem_{p.id}"
            )
        builder.button(text="🔙 Назад", callback_data="back_to_menu")
        builder.adjust(1)

        await callback.message.answer(
            "📋 **Твои проблемы:**",
            reply_markup=builder.as_markup()
        )

    await callback.answer()

@router.callback_query(F.data.startswith("view_problem_"))
async def view_problem_detail(callback: CallbackQuery):
    """Show problem details"""
    problem_id = int(callback.data.split("_")[2])

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from bot.database.models import Problem

        result = await session.execute(
            select(Problem).where(Problem.id == problem_id)
        )
        problem = result.scalar_one_or_none()

        if not problem:
            await callback.answer("Проблема не найдена", show_alert=True)
            return

        text = f"📝 **Проблема:**\n{problem.title}\n\n"

        if problem.root_cause:
            text += f"🎯 **Причина:**\n{problem.root_cause}\n\n"

        if problem.action_plan:
            plan = json.loads(problem.action_plan)
            text += "📋 **План:**\n"
            for action in plan.get('immediate', [])[:2]:
                text += f"□ {action}\n"

        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 К списку", callback_data="my_problems")

        await callback.message.answer(text, reply_markup=builder.as_markup())

    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Return to main menu"""
    from bot.handlers.start import cmd_start
    await cmd_start(callback.message)
    await callback.answer()
