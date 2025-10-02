from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id
from bot.database.models import Payment

router = Router()

# Pricing in Telegram Stars
PACKAGES = {
    'starter': {'solutions': 5, 'price': 100, 'discussion_limit': 10},
    'medium': {'solutions': 15, 'price': 250, 'discussion_limit': 15},
    'large': {'solutions': 30, 'price': 500, 'discussion_limit': 25},
    'discussion_5': {'discussions': 5, 'price': 50},
    'discussion_15': {'discussions': 15, 'price': 120},
}


@router.callback_query(F.data == "buy_solutions")
async def show_solution_packages(callback: CallbackQuery):
    """Show solution package options"""
    text = """💳 **Пакеты решений**

Выбери подходящий пакет:

**🟢 Starter** — 5 решений
• Цена: 100 ⭐️ (~$2)
• Лимит вопросов в обсуждении: 10

**🔵 Medium** — 15 решений
• Цена: 250 ⭐️ (~$5)
• Лимит вопросов в обсуждении: 15

**🟣 Large** — 30 решений
• Цена: 500 ⭐️ (~$10)
• Лимит вопросов в обсуждении: 25

Решения не сгорают — используй когда удобно!"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Starter (100⭐️)", callback_data="buy_starter")
    builder.button(text="🔵 Medium (250⭐️)", callback_data="buy_medium")
    builder.button(text="🟣 Large (500⭐️)", callback_data="buy_large")
    builder.button(text="💬 Купить вопросы для обсуждения", callback_data="buy_discussions")
    builder.adjust(1)

    from bot.keyboards import get_main_menu_keyboard
    await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.message.answer("Меню:", reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "buy_discussions")
async def show_discussion_packages(callback: CallbackQuery):
    """Show discussion question packages"""
    text = """💬 **Пакеты вопросов для обсуждения**

После каждого решения можно задать дополнительные вопросы.
Купи пакет вопросов для углубленного анализа:

**📦 Малый** — 5 вопросов
• Цена: 50 ⭐️ (~$1)

**📦 Средний** — 15 вопросов
• Цена: 120 ⭐️ (~$2.4)

Вопросы добавляются к твоему счёту и не сгорают!"""

    builder = InlineKeyboardBuilder()
    builder.button(text="📦 5 вопросов (50⭐️)", callback_data="buy_discussion_5")
    builder.button(text="📦 15 вопросов (120⭐️)", callback_data="buy_discussion_15")
    builder.button(text="🔙 К пакетам решений", callback_data="buy_solutions")
    builder.adjust(1)

    from bot.keyboards import get_main_menu_keyboard
    await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.message.answer("Меню:", reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "buy_starter")
async def buy_starter_package(callback: CallbackQuery):
    """Purchase Starter package"""
    await initiate_package_payment(
        callback,
        package_type='starter',
        title="Starter Package - 5 решений",
        description="5 решений проблем + лимит 10 вопросов в обсуждении"
    )


@router.callback_query(F.data == "buy_medium")
async def buy_medium_package(callback: CallbackQuery):
    """Purchase Medium package"""
    await initiate_package_payment(
        callback,
        package_type='medium',
        title="Medium Package - 15 решений",
        description="15 решений проблем + лимит 15 вопросов в обсуждении"
    )


@router.callback_query(F.data == "buy_large")
async def buy_large_package(callback: CallbackQuery):
    """Purchase Large package"""
    await initiate_package_payment(
        callback,
        package_type='large',
        title="Large Package - 30 решений",
        description="30 решений проблем + лимит 25 вопросов в обсуждении"
    )


@router.callback_query(F.data == "buy_discussion_5")
async def buy_discussion_5(callback: CallbackQuery):
    """Purchase 5 discussion questions"""
    await initiate_package_payment(
        callback,
        package_type='discussion_5',
        title="5 вопросов для обсуждения",
        description="5 дополнительных вопросов после решения проблемы"
    )


@router.callback_query(F.data == "buy_discussion_15")
async def buy_discussion_15(callback: CallbackQuery):
    """Purchase 15 discussion questions"""
    await initiate_package_payment(
        callback,
        package_type='discussion_15',
        title="15 вопросов для обсуждения",
        description="15 дополнительных вопросов после решения проблемы"
    )


async def initiate_package_payment(callback: CallbackQuery, package_type: str, title: str, description: str):
    """Generic payment initiation"""
    package = PACKAGES[package_type]
    prices = [LabeledPrice(label=title, amount=package['price'])]

    await callback.message.answer_invoice(
        title=title,
        description=description,
        payload=f"{package_type}_{callback.from_user.id}",
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
    payload = payment_info.invoice_payload
    package_type = payload.split("_")[0]

    # Save to database and update user credits
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

        # Update user credits based on package type
        package = PACKAGES[package_type]

        if 'solutions' in package:
            # Solution package
            user.problems_remaining += package['solutions']
            user.last_purchased_package = package_type
            success_msg = f"""🎉 **Спасибо за покупку!**

✅ Добавлено решений: {package['solutions']}
💳 Всего доступно: {user.problems_remaining}
💬 Лимит вопросов в обсуждении: {package['discussion_limit']}

Готов решать проблемы! 🚀"""
        else:
            # Discussion package
            user.discussion_credits += package['discussions']
            success_msg = f"""🎉 **Спасибо за покупку!**

✅ Добавлено вопросов: {package['discussions']}
💬 Всего доступно: {user.discussion_credits}

Теперь можешь глубже обсуждать решения! 💡"""

        await session.commit()

    from bot.keyboards import get_main_menu_keyboard
    await message.answer(success_msg, reply_markup=get_main_menu_keyboard())
