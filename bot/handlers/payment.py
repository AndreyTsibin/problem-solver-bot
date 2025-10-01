from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id, update_user_premium
from bot.database.models import Payment

router = Router()

PREMIUM_PRICE = 100  # Telegram Stars

@router.callback_query(F.data == "premium")
async def show_premium_offer(callback: CallbackQuery):
    """Show premium features and pricing"""
    text = """
💎 **Премиум подписка**

**Что получишь:**
✅ Безлимитные анализы проблем
✅ Приоритетная обработка
✅ Экспорт решений (скоро)

**Цена:** 100 ⭐️ Telegram Stars (~$2)
**Навсегда** (не подписка)
"""

    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Купить за 100 ⭐️", callback_data="buy_premium")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)

    await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "buy_premium")
async def initiate_payment(callback: CallbackQuery):
    """Send invoice for premium"""
    prices = [LabeledPrice(label="Премиум доступ", amount=PREMIUM_PRICE)]

    await callback.message.answer_invoice(
        title="Problem Solver Premium",
        description="Безлимитные анализы проблем",
        payload=f"premium_{callback.from_user.id}",
        currency="XTR",  # Telegram Stars
        prices=prices
    )

    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Validate payment before charging"""
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Handle successful payment"""
    payment_info = message.successful_payment

    # Save to database
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        # Create payment record
        payment = Payment(
            user_id=user.id,
            amount=payment_info.total_amount,
            currency=payment_info.currency,
            provider="telegram_stars",
            status="completed",
            telegram_payment_id=payment_info.telegram_payment_charge_id
        )
        session.add(payment)

        # Activate premium
        await update_user_premium(session, user.id, True)
        await session.commit()

    await message.answer(
        "🎉 **Спасибо за покупку!**\n\n"
        "✅ Премиум активирован\n"
        "Теперь у тебя безлимитные анализы проблем!"
    )
