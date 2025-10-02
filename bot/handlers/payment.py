"""Payment handlers using YooKassa (rubles)"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id
from bot.database.models import Payment as PaymentModel
from bot.services.yookassa_service import YooKassaService
from datetime import datetime
import structlog

router = Router()
logger = structlog.get_logger()

# Pricing in Russian Rubles
PACKAGES = {
    'starter': {'solutions': 5, 'price': 250, 'discussion_limit': 10, 'name': 'Starter'},
    'medium': {'solutions': 15, 'price': 600, 'discussion_limit': 15, 'name': 'Medium'},
    'large': {'solutions': 30, 'price': 1200, 'discussion_limit': 25, 'name': 'Large'},
    'discussion_5': {'discussions': 5, 'price': 100, 'name': '5 вопросов'},
    'discussion_15': {'discussions': 15, 'price': 240, 'name': '15 вопросов'},
    # Subscription plans (monthly recurring)
    'subscription_standard': {
        'solutions': 15,
        'price': 599,
        'discussion_limit': 15,
        'plan': 'standard',
        'name': 'Подписка Стандарт'
    },
    'subscription_premium': {
        'solutions': 30,
        'price': 999,
        'discussion_limit': 25,
        'plan': 'premium',
        'name': 'Подписка Премиум'
    },
}


@router.callback_query(F.data == "buy_solutions")
async def show_solution_packages(callback: CallbackQuery):
    """Show solution package and subscription options"""
    text = """💳 <b>Тарифы и пакеты</b>

<b>📆 ПОДПИСКИ (ежемесячно):</b>

🔷 <b>Стандарт</b> — 599₽/мес
• 15 решений каждый месяц
• 15 вопросов на обсуждение
• История за 3 месяца

💎 <b>Премиум</b> — 999₽/мес
• 30 решений каждый месяц
• 25 вопросов на обсуждение
• Полная история решений
• Приоритетная обработка

━━━━━━━━━━━━━━━

<b>💰 РАЗОВЫЕ ПАКЕТЫ:</b>

🟢 <b>Starter</b> — 250₽
• 5 решений
• 10 вопросов на обсуждение

🔵 <b>Medium</b> — 600₽
• 15 решений
• 15 вопросов на обсуждение

🟣 <b>Large</b> — 1200₽
• 30 решений
• 25 вопросов на обсуждение

<i>Решения не сгорают — используй когда удобно!</i>"""

    builder = InlineKeyboardBuilder()
    # Subscriptions
    builder.button(text="🔷 Подписка Стандарт (599₽/мес)", callback_data="buy_subscription_standard")
    builder.button(text="💎 Подписка Премиум (999₽/мес)", callback_data="buy_subscription_premium")
    # One-time packages
    builder.button(text="🟢 Starter (250₽)", callback_data="buy_starter")
    builder.button(text="🔵 Medium (600₽)", callback_data="buy_medium")
    builder.button(text="🟣 Large (1200₽)", callback_data="buy_large")
    builder.button(text="💬 Купить вопросы для обсуждения", callback_data="buy_discussions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "buy_discussions")
async def show_discussion_packages(callback: CallbackQuery):
    """Show discussion question packages"""
    text = """💬 <b>Пакеты вопросов для обсуждения</b>

После каждого решения можно задать дополнительные вопросы.
Выбери пакет:

🟢 <b>Малый</b> — 100₽
• 5 дополнительных вопросов

🔵 <b>Средний</b> — 240₽ (скидка 20₽!)
• 15 дополнительных вопросов

<i>Вопросы не сгорают — используй когда нужно!</i>"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 5 вопросов (100₽)", callback_data="buy_discussion_5")
    builder.button(text="🔵 15 вопросов (240₽)", callback_data="buy_discussion_15")
    builder.button(text="◀️ Назад", callback_data="buy_solutions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


# Payment handlers for each package
@router.callback_query(F.data == "buy_starter")
async def buy_starter_package(callback: CallbackQuery):
    """Purchase Starter package"""
    await initiate_yookassa_payment(
        callback,
        package_type='starter',
        description="Пакет Starter: 5 решений + 10 вопросов на обсуждение"
    )


@router.callback_query(F.data == "buy_medium")
async def buy_medium_package(callback: CallbackQuery):
    """Purchase Medium package"""
    await initiate_yookassa_payment(
        callback,
        package_type='medium',
        description="Пакет Medium: 15 решений + 15 вопросов на обсуждение"
    )


@router.callback_query(F.data == "buy_large")
async def buy_large_package(callback: CallbackQuery):
    """Purchase Large package"""
    await initiate_yookassa_payment(
        callback,
        package_type='large',
        description="Пакет Large: 30 решений + 25 вопросов на обсуждение"
    )


@router.callback_query(F.data == "buy_discussion_5")
async def buy_discussion_5(callback: CallbackQuery):
    """Purchase 5 discussion questions"""
    await initiate_yookassa_payment(
        callback,
        package_type='discussion_5',
        description="5 дополнительных вопросов для обсуждения"
    )


@router.callback_query(F.data == "buy_discussion_15")
async def buy_discussion_15(callback: CallbackQuery):
    """Purchase 15 discussion questions"""
    await initiate_yookassa_payment(
        callback,
        package_type='discussion_15',
        description="15 дополнительных вопросов для обсуждения"
    )


@router.callback_query(F.data == "buy_subscription_standard")
async def buy_subscription_standard(callback: CallbackQuery):
    """Purchase Standard monthly subscription"""
    await initiate_yookassa_payment(
        callback,
        package_type='subscription_standard',
        description="Подписка Стандарт: 15 решений/мес + 15 вопросов (ежемесячно)"
    )


@router.callback_query(F.data == "buy_subscription_premium")
async def buy_subscription_premium(callback: CallbackQuery):
    """Purchase Premium monthly subscription"""
    await initiate_yookassa_payment(
        callback,
        package_type='subscription_premium',
        description="Подписка Премиум: 30 решений/мес + 25 вопросов + приоритет (ежемесячно)"
    )


async def initiate_yookassa_payment(callback: CallbackQuery, package_type: str, description: str):
    """
    Initiate payment via YooKassa

    Args:
        callback: Telegram callback query
        package_type: Type of package being purchased
        description: Payment description
    """
    try:
        package = PACKAGES[package_type]
        user_id = callback.from_user.id

        # Create payment in YooKassa
        yookassa = YooKassaService()
        payment_data = await yookassa.create_payment(
            amount=package['price'],
            description=description,
            user_telegram_id=user_id,
            package_type=package_type,
            return_url=f"https://t.me/{callback.bot.me.username}"
        )

        # Save payment to database
        async with AsyncSessionLocal() as session:
            user = await get_user_by_telegram_id(session, user_id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            payment = PaymentModel(
                user_id=user.id,
                package_type=package_type,
                amount=package['price'],
                currency='RUB',
                status='pending',
                payment_id=payment_data['payment_id'],
                created_at=datetime.utcnow()
            )
            session.add(payment)
            await session.commit()

        # Send payment link to user
        text = (
            f"💳 <b>Оплата: {package['name']}</b>\n\n"
            f"Сумма: <b>{package['price']}₽</b>\n"
            f"{description}\n\n"
            f"Нажми кнопку ниже для оплаты через ЮКассу:"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💳 Оплатить",
                url=payment_data['confirmation_url']
            )],
            [InlineKeyboardButton(
                text="🔍 Проверить оплату",
                callback_data=f"check_payment_{payment_data['payment_id']}"
            )]
        ])

        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

        logger.info(
            "payment_initiated",
            user_id=user_id,
            package=package_type,
            amount=package['price'],
            payment_id=payment_data['payment_id']
        )

    except Exception as e:
        logger.error("payment_initiation_error", error=str(e), user_id=callback.from_user.id)
        await callback.answer(
            "❌ Ошибка при создании платежа. Попробуйте позже.",
            show_alert=True
        )


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery):
    """Check payment status in YooKassa"""
    try:
        payment_id = callback.data.split("_", 2)[2]

        yookassa = YooKassaService()
        payment_status = await yookassa.check_payment_status(payment_id)

        if payment_status['paid']:
            # Payment successful - activate package
            await process_successful_payment(callback, payment_status)
        else:
            await callback.answer(
                f"⏳ Платёж в статусе: {payment_status['status']}\n"
                "Попробуйте проверить позже.",
                show_alert=True
            )

    except Exception as e:
        logger.error("payment_check_error", error=str(e), payment_id=payment_id)
        await callback.answer("❌ Ошибка при проверке платежа", show_alert=True)


async def process_successful_payment(callback: CallbackQuery, payment_status: dict):
    """Process successful payment and activate package"""
    try:
        metadata = payment_status['metadata']
        user_id = int(metadata['user_telegram_id'])
        package_type = metadata['package_type']
        package = PACKAGES[package_type]

        async with AsyncSessionLocal() as session:
            from bot.database.crud_subscriptions import create_subscription

            user = await get_user_by_telegram_id(session, user_id)
            if not user:
                return

            # Update payment status
            payment = await session.execute(
                f"SELECT * FROM payments WHERE payment_id = '{payment_status['payment_id']}'"
            )
            # Mark as completed

            # Activate package based on type
            if package_type.startswith('subscription_'):
                # Create subscription
                subscription = await create_subscription(
                    session,
                    user_id=user.id,
                    plan=package['plan'],
                    price=package['price']
                )
                user.problems_remaining += package['solutions']
                user.subscription_id = subscription.id

                success_msg = (
                    f"✅ <b>Подписка активирована!</b>\n\n"
                    f"Тариф: {package['name']}\n"
                    f"Решений добавлено: {package['solutions']}\n"
                    f"Лимит вопросов: {package['discussion_limit']}\n\n"
                    f"Подписка будет автоматически продлеваться каждый месяц."
                )

            elif package_type.startswith('discussion_'):
                # Add discussion credits
                user.discussion_credits += package['discussions']

                success_msg = (
                    f"✅ <b>Вопросы добавлены!</b>\n\n"
                    f"Дополнительных вопросов: +{package['discussions']}\n"
                    f"Всего вопросов: {user.discussion_credits}"
                )

            else:
                # One-time package
                user.problems_remaining += package['solutions']
                user.last_purchased_package = package_type

                success_msg = (
                    f"✅ <b>Пакет активирован!</b>\n\n"
                    f"Решений добавлено: +{package['solutions']}\n"
                    f"Всего решений: {user.problems_remaining}\n"
                    f"Лимит вопросов: {package['discussion_limit']}"
                )

            await session.commit()

            await callback.message.answer(success_msg, parse_mode="HTML")
            await callback.answer("✅ Оплата успешна!")

            logger.info(
                "payment_processed",
                user_id=user_id,
                package=package_type,
                amount=payment_status['amount']
            )

    except Exception as e:
        logger.error("payment_processing_error", error=str(e))
        await callback.answer("❌ Ошибка при активации пакета", show_alert=True)
