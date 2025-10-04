"""Subscription management handlers"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user
from bot.database.crud_subscriptions import get_active_subscription, cancel_subscription
from bot.config import SUBSCRIPTION_PLANS
from datetime import datetime
import structlog

logger = structlog.get_logger()
router = Router()


@router.message(Command("subscription"))
async def handle_subscription_command(message: Message):
    """Handle /subscription command - show subscription status"""
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name or "Пользователь"

    try:
        async with AsyncSessionLocal() as session:
            # Get or create user
            user = await get_or_create_user(
                session, telegram_id, username, first_name
            )

            # Get active subscription
            subscription = await get_active_subscription(session, user.id)

            if subscription:
                # User has active subscription
                plan_info = SUBSCRIPTION_PLANS.get(subscription.plan, {})
                plan_name = plan_info.get('name', subscription.plan.capitalize())

                # Calculate days until renewal
                days_until = (subscription.next_billing_date - datetime.utcnow()).days

                text = (
                    f"💎 <b>Активная подписка</b>\n\n"
                    f"📦 Тариф: <b>{plan_name}</b>\n"
                    f"💰 Цена: {subscription.price} ⭐️/месяц\n"
                    f"📅 Следующее списание: {subscription.next_billing_date.strftime('%d.%m.%Y')}\n"
                    f"⏰ Осталось дней: {days_until}\n\n"
                    f"✅ Доступно решений: {user.problems_remaining}\n"
                    f"💬 Лимит вопросов: {subscription.discussion_limit}\n\n"
                    f"Подписка продлевается автоматически каждый месяц."
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="⬆️ Повысить тариф",
                        callback_data="upgrade_subscription"
                    )],
                    [InlineKeyboardButton(
                        text="❌ Отменить подписку",
                        callback_data="cancel_subscription_confirm"
                    )]
                ])

            else:
                # User has no active subscription
                text = (
                    f"💳 <b>Решений на балансе:</b> {user.problems_remaining}\n\n"
                    f"Оформи подписку для безлимитного доступа!\n\n"
                    f"<b>🔸 СТАНДАРТ</b> — 599₽/месяц\n"
                    f"- 15 решений каждый месяц\n"
                    f"- 15 вопросов в обсуждении\n"
                    f"- История за 3 месяца\n\n"
                    f"<b>💎 ПРЕМИУМ</b> — 999₽/месяц\n"
                    f"- 30 решений каждый месяц\n"
                    f"- 25 вопросов в обсуждении\n"
                    f"- Полная история\n"
                    f"- Приоритетная обработка\n\n"
                    f"💡 Решения обновляются автоматически каждый месяц!"
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🔸 Стандарт (599₽)",
                        callback_data="select_package_subscription_standard"
                    )],
                    [InlineKeyboardButton(
                        text="💎 Премиум (999₽)",
                        callback_data="select_package_subscription_premium"
                    )],
                    [InlineKeyboardButton(
                        text="💸 Разовые пакеты",
                        callback_data="show_packages"
                    )]
                ])

            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logger.error("subscription_command_error", error=str(e), user_id=telegram_id)
        await message.answer(
            "❌ Произошла ошибка при загрузке информации о подписке. "
            "Попробуйте позже."
        )


@router.callback_query(F.data == "cancel_subscription_confirm")
async def handle_cancel_subscription_confirm(callback: CallbackQuery):
    """Show cancellation confirmation"""
    text = (
        "⚠️ <b>Отменить подписку?</b>\n\n"
        "Твоя подписка будет отменена, но продолжит работать до конца "
        "оплаченного периода.\n\n"
        "Оставшиеся решения останутся доступны."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Да, отменить",
            callback_data="cancel_subscription_confirmed"
        )],
        [InlineKeyboardButton(
            text="❌ Нет, оставить",
            callback_data="cancel_subscription_abort"
        )]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "cancel_subscription_confirmed")
async def handle_cancel_subscription_confirmed(callback: CallbackQuery):
    """Cancel subscription after confirmation"""
    telegram_id = callback.from_user.id

    try:
        async with AsyncSessionLocal() as session:
            from bot.database.crud import get_user_by_telegram_id

            user = await get_user_by_telegram_id(session, telegram_id)
            if not user or not user.subscription_id:
                await callback.answer("❌ Подписка не найдена", show_alert=True)
                return

            subscription = await get_active_subscription(session, user.id)
            if not subscription:
                await callback.answer("❌ Активная подписка не найдена", show_alert=True)
                return

            # Cancel subscription
            await cancel_subscription(session, subscription.id)

            text = (
                f"✅ <b>Подписка отменена</b>\n\n"
                f"Твоя подписка будет работать до {subscription.next_billing_date.strftime('%d.%m.%Y')}.\n"
                f"Автопродление отключено.\n\n"
                f"Ты можешь оформить новую подписку в любой момент: /subscription"
            )

            await callback.message.edit_text(text, parse_mode="HTML")
            await callback.answer("Подписка отменена")

            logger.info(f"Subscription cancelled for user {telegram_id}")

    except Exception as e:
        logger.error("cancel_subscription_error", error=str(e), user_id=telegram_id)
        await callback.answer("❌ Ошибка при отмене подписки", show_alert=True)


@router.callback_query(F.data == "cancel_subscription_abort")
async def handle_cancel_subscription_abort(callback: CallbackQuery):
    """Abort subscription cancellation"""
    await callback.message.edit_text(
        "✅ Отмена отменена! Твоя подписка остаётся активной.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "upgrade_subscription")
async def handle_upgrade_subscription(callback: CallbackQuery):
    """Show upgrade options"""
    telegram_id = callback.from_user.id

    try:
        async with AsyncSessionLocal() as session:
            from bot.database.crud import get_user_by_telegram_id

            user = await get_user_by_telegram_id(session, telegram_id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            subscription = await get_active_subscription(session, user.id)
            if not subscription:
                await callback.answer("❌ Активная подписка не найдена", show_alert=True)
                return

            current_plan = subscription.plan

            if current_plan == 'standard':
                text = (
                    "⬆️ <b>Повышение тарифа</b>\n\n"
                    "Переходи на <b>Премиум</b> и получи:\n\n"
                    "• 30 решений/месяц (вместо 15)\n"
                    "• 25 вопросов в обсуждении (вместо 15)\n"
                    "• Полная история (вместо 3 месяцев)\n"
                    "• Приоритетная обработка\n\n"
                    "💰 Доплата: 200₽/месяц (всего 999₽)"
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Повысить до Премиум",
                        callback_data="upgrade_to_premium"
                    )],
                    [InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data="back_to_subscription"
                    )]
                ])

            else:  # premium
                text = (
                    "✅ <b>У тебя максимальный тариф!</b>\n\n"
                    "Ты уже используешь тариф <b>Премиум</b> — "
                    "лучшее что у нас есть! 🎉"
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data="back_to_subscription"
                    )]
                ])

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()

    except Exception as e:
        logger.error("upgrade_subscription_error", error=str(e), user_id=telegram_id)
        await callback.answer("❌ Ошибка при загрузке информации", show_alert=True)


@router.callback_query(F.data == "upgrade_to_premium")
async def handle_upgrade_to_premium(callback: CallbackQuery):
    """Upgrade from standard to premium (requires payment handler)"""
    # This will be handled by payment.py
    # For now, redirect to payment flow
    await callback.answer(
        "Функция повышения тарифа будет добавлена в следующей версии!",
        show_alert=True
    )


@router.callback_query(F.data == "back_to_subscription")
async def handle_back_to_subscription(callback: CallbackQuery):
    """Go back to subscription info"""
    # Re-trigger subscription command
    from aiogram.types import Message as MessageType

    # Create a pseudo-message to re-use the command handler
    await handle_subscription_command(callback.message)
    await callback.answer()


# show_packages handler moved to payment.py to avoid duplication
