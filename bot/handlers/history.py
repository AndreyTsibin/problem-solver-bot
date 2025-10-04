from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id, get_user_problems
from bot.utils.text import prepare_problem_text

router = Router()

@router.callback_query(F.data == "my_problems")
async def show_problems_list(callback: CallbackQuery):
    """Show user's problems history"""
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        problems = await get_user_problems(session, user.id, limit=10)

        if not problems:
            await callback.message.answer("📭 У тебя пока нет решённых задач")
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
        builder.adjust(1)

        from bot.keyboards import get_main_menu_keyboard
        await callback.message.answer(
            "📖 История решений:",
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

        # Always use safe text preparation to strip markdown
        text = prepare_problem_text(
            title=problem.title,
            root_cause=problem.root_cause,
            action_plan=problem.action_plan,
            max_plan_length=1500
        )

        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 К списку", callback_data="my_problems")
        builder.adjust(1)

        await callback.message.answer(text, reply_markup=builder.as_markup())

    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Return to main menu (legacy - now menu always visible)"""
    from bot.keyboards import get_main_menu_keyboard
    await callback.message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())
    await callback.answer()
