"""Payment handlers supporting both YooKassa (rubles) and Telegram Stars"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id
from bot.database.models import Payment as PaymentModel
from bot.services.yookassa_service import YooKassaService
from bot.config import (
    ENABLE_YOOKASSA,
    ENABLE_TELEGRAM_STARS,
    PACKAGES_YOOKASSA,
    PACKAGES_STARS
)
from datetime import datetime
import structlog

router = Router()
logger = structlog.get_logger()


# ============================================================================
# LEVEL 0: Purchase type selection (NEW - subscriptions vs packages)
# ============================================================================

@router.callback_query(F.data == "buy_solutions")
async def show_purchase_type_selection(callback: CallbackQuery):
    """Show purchase type selection: subscriptions vs one-time packages (Level 0)"""
    text = """💳 <b>Что тебе удобнее?</b>

<b>📅 Подписка</b>
• Автопродление каждый месяц
• Не нужно каждый раз покупать
• Выгоднее при регулярном использовании

<b>💰 Разовые пакеты</b>
• Покупаешь один раз
• Решения не сгорают
• Используешь когда удобно

<b>💬 Вопросы для обсуждения</b>
• Дополнительные вопросы после решения
• Для более глубокого анализа"""

    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Подписки", callback_data="show_subscriptions")
    builder.button(text="💰 Разовые пакеты", callback_data="show_packages")
    builder.button(text="💬 Вопросы для обсуждения", callback_data="buy_discussions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


# ============================================================================
# LEVEL 1: Package selection (subscriptions OR packages separately)
# ============================================================================

@router.callback_query(F.data == "show_subscriptions")
async def show_subscriptions(callback: CallbackQuery):
    """Show only subscription options (Level 1)"""
    text = """📅 <b>Выбери подписку</b>

<b>🔸 Стандарт</b>
• 15 решений каждый месяц
• 15 вопросов на обсуждение
• История за 3 месяца
• Автопродление

<b>💎 Премиум</b>
• 30 решений каждый месяц
• 25 вопросов на обсуждение
• Полная история решений
• Приоритетная обработка
• Автопродление

<i>💡 Подписка продлевается автоматически</i>"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🔸 Стандарт", callback_data="select_package_subscription_standard")
    builder.button(text="💎 Премиум", callback_data="select_package_subscription_premium")
    builder.button(text="◀️ Назад", callback_data="buy_solutions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "show_packages")
async def show_packages(callback: CallbackQuery):
    """Show only one-time packages (Level 1)"""
    text = """💰 <b>Выбери пакет</b>

<b>📒 Стартовый</b>
• 5 решений проблем
• 10 вопросов на обсуждение

<b>📗 Средний</b>
• 15 решений проблем
• 15 вопросов на обсуждение

<b>📕 Большой</b>
• 30 решений проблем
• 25 вопросов на обсуждение

<i>💡 Решения не сгорают — используй когда удобно!</i>"""

    builder = InlineKeyboardBuilder()
    builder.button(text="📒 Стартовый", callback_data="select_package_starter")
    builder.button(text="📗 Средний", callback_data="select_package_medium")
    builder.button(text="📕 Большой", callback_data="select_package_large")
    builder.button(text="◀️ Назад", callback_data="buy_solutions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "buy_discussions")
async def show_discussion_packages(callback: CallbackQuery):
    """Show discussion question packages (Level 1)"""
    text = """💬 <b>Пакеты вопросов для обсуждения</b>

После каждого решения можно задать дополнительные вопросы.
Выбери пакет:

<b>Малый</b>
• 5 дополнительных вопросов

<b>Средний</b>
• 15 дополнительных вопросов

<i>💡 Вопросы не сгорают — используй когда нужно!</i>"""

    builder = InlineKeyboardBuilder()
    builder.button(text="💬 5 вопросов", callback_data="select_package_discussion_5")
    builder.button(text="💬 15 вопросов", callback_data="select_package_discussion_15")
    builder.button(text="◀️ К пакетам решений", callback_data="buy_solutions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


# ============================================================================
# LEVEL 2: Payment method selection (with prices)
# ============================================================================

@router.callback_query(F.data.startswith("select_package_"))
async def show_payment_methods(callback: CallbackQuery):
    """Show payment method selection (Level 2) for chosen package"""
    package_type = callback.data.replace("select_package_", "")

    # Get package info from both pricing tables
    yookassa_package = PACKAGES_YOOKASSA.get(package_type)
    stars_package = PACKAGES_STARS.get(package_type)

    if not yookassa_package and not stars_package:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    # Build description based on package type
    package_name = yookassa_package['name'] if yookassa_package else stars_package['name']

    if package_type.startswith('subscription_'):
        description = f"<b>{package_name}</b>\n"
        solutions = yookassa_package.get('solutions', 0)
        discussion = yookassa_package.get('discussion_limit', 0)
        description += f"• {solutions} решений каждый месяц\n"
        description += f"• {discussion} вопросов на обсуждение\n"
        description += f"• Автоматическое продление"
    elif package_type.startswith('discussion_'):
        discussions = yookassa_package.get('discussions', 0)
        description = f"<b>{package_name}</b>\n"
        description += f"• {discussions} дополнительных вопросов"
    else:
        # One-time package
        solutions = yookassa_package.get('solutions', 0)
        discussion = yookassa_package.get('discussion_limit', 0)
        description = f"<b>{package_name}</b>\n"
        description += f"• {solutions} решений проблем\n"
        description += f"• {discussion} вопросов на обсуждение"

    text = f"""💳 <b>Выбери способ оплаты</b>

{description}

<b>Доступные способы оплаты:</b>"""

    builder = InlineKeyboardBuilder()

    # Add YooKassa button if enabled
    if ENABLE_YOOKASSA and yookassa_package:
        yookassa_price = yookassa_package['price']
        builder.button(
            text=f"💳 Банковская карта ({yookassa_price}₽)",
            callback_data=f"pay_yookassa_{package_type}"
        )

    # Add Telegram Stars button if enabled
    if ENABLE_TELEGRAM_STARS and stars_package:
        stars_price = stars_package['price']
        builder.button(
            text=f"⭐️ Telegram Stars ({stars_price}⭐️)",
            callback_data=f"pay_stars_{package_type}"
        )

    # Back button
    if package_type.startswith('discussion_'):
        builder.button(text="◀️ Назад", callback_data="buy_discussions")
    else:
        builder.button(text="◀️ Назад", callback_data="buy_solutions")

    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


# ============================================================================
# YooKassa Payment Flow
# ============================================================================

@router.callback_query(F.data.startswith("pay_yookassa_"))
async def initiate_yookassa_payment(callback: CallbackQuery):
    """Initiate payment via YooKassa"""
    package_type = callback.data.replace("pay_yookassa_", "")
    package = PACKAGES_YOOKASSA.get(package_type)

    if not package:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    # Build description
    if package_type.startswith('subscription_'):
        description = f"Подписка {package['name']}: {package['solutions']} решений/мес + {package['discussion_limit']} вопросов (ежемесячно)"
    elif package_type.startswith('discussion_'):
        description = f"{package['discussions']} дополнительных вопросов для обсуждения"
    else:
        description = f"Пакет {package['name']}: {package['solutions']} решений + {package['discussion_limit']} вопросов"

    try:
        user_id = callback.from_user.id

        # Create payment in YooKassa
        yookassa = YooKassaService()
        bot_info = await callback.bot.me()
        payment_data = await yookassa.create_payment(
            amount=package['price'],
            description=description,
            user_telegram_id=user_id,
            package_type=package_type,
            return_url=f"https://t.me/{bot_info.username}"
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
                provider='yookassa',
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
            "yookassa_payment_initiated",
            user_id=user_id,
            package=package_type,
            amount=package['price'],
            payment_id=payment_data['payment_id']
        )

    except Exception as e:
        logger.error("yookassa_payment_error", error=str(e), user_id=callback.from_user.id)
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
            await process_successful_yookassa_payment(callback, payment_status)
        else:
            await callback.answer(
                f"⏳ Платёж в статусе: {payment_status['status']}\n"
                "Попробуйте проверить позже.",
                show_alert=True
            )

    except Exception as e:
        logger.error("payment_check_error", error=str(e), payment_id=payment_id)
        await callback.answer("❌ Ошибка при проверке платежа", show_alert=True)


async def process_successful_yookassa_payment(callback: CallbackQuery, payment_status: dict):
    """Process successful YooKassa payment and activate package"""
    try:
        metadata = payment_status['metadata']
        user_id = int(metadata['user_telegram_id'])
        package_type = metadata['package_type']
        package = PACKAGES_YOOKASSA[package_type]

        async with AsyncSessionLocal() as session:
            from bot.database.crud_subscriptions import create_subscription

            user = await get_user_by_telegram_id(session, user_id)
            if not user:
                return

            # Activate package
            success_msg = await activate_package(session, user, package, package_type)
            await session.commit()

            await callback.message.answer(success_msg, parse_mode="HTML")
            await callback.answer("✅ Оплата успешна!")

            logger.info(
                "yookassa_payment_processed",
                user_id=user_id,
                package=package_type,
                amount=payment_status['amount']
            )

    except Exception as e:
        logger.error("yookassa_payment_processing_error", error=str(e))
        await callback.answer("❌ Ошибка при активации пакета", show_alert=True)


# ============================================================================
# Telegram Stars Payment Flow
# ============================================================================

@router.callback_query(F.data.startswith("pay_stars_"))
async def initiate_stars_payment(callback: CallbackQuery):
    """Initiate payment via Telegram Stars"""
    package_type = callback.data.replace("pay_stars_", "")
    package = PACKAGES_STARS.get(package_type)

    if not package:
        await callback.answer("❌ Пакет не найден", show_alert=True)
        return

    # Build title and description
    if package_type.startswith('subscription_'):
        title = f"Подписка {package['name']}"
        description = f"{package['solutions']} решений/мес + {package['discussion_limit']} вопросов на обсуждение (автопродление)"
    elif package_type.startswith('discussion_'):
        title = f"{package['discussions']} вопросов"
        description = f"{package['discussions']} дополнительных вопросов для обсуждения решений"
    else:
        title = f"Пакет {package['name']}"
        description = f"{package['solutions']} решений + {package['discussion_limit']} вопросов на обсуждение"

    prices = [LabeledPrice(label=title, amount=package['price'])]

    try:
        await callback.message.answer_invoice(
            title=title,
            description=description,
            payload=f"{package_type}_{callback.from_user.id}",
            currency="XTR",  # Telegram Stars
            prices=prices
        )
        await callback.answer()

        logger.info(
            "stars_payment_initiated",
            user_id=callback.from_user.id,
            package=package_type,
            amount=package['price']
        )

    except Exception as e:
        logger.error("stars_payment_error", error=str(e), user_id=callback.from_user.id)
        await callback.answer("❌ Ошибка при создании платежа", show_alert=True)


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Validate payment before charging (Telegram Stars)"""
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_stars_payment(message: Message):
    """Handle successful Telegram Stars payment"""
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    package_type = payload.rsplit("_", 1)[0]  # Extract package type from payload

    package = PACKAGES_STARS.get(package_type)
    if not package:
        logger.error("stars_package_not_found", package_type=package_type)
        return

    # Save to database and update user credits
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        if not user:
            logger.error("stars_user_not_found", telegram_id=message.from_user.id)
            return

        # Create payment record
        payment = PaymentModel(
            user_id=user.id,
            package_type=package_type,
            amount=payment_info.total_amount,
            currency=payment_info.currency,
            provider="telegram_stars",
            status="completed",
            telegram_payment_id=payment_info.telegram_payment_charge_id,
            created_at=datetime.utcnow()
        )
        session.add(payment)

        # Activate package
        success_msg = await activate_package(session, user, package, package_type)
        await session.commit()

    from bot.keyboards import get_main_menu_keyboard
    await message.answer(success_msg, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")

    logger.info(
        "stars_payment_processed",
        user_id=message.from_user.id,
        package=package_type,
        amount=payment_info.total_amount
    )


# ============================================================================
# Shared helper: Activate package for both payment providers
# ============================================================================

async def activate_package(session, user, package: dict, package_type: str) -> str:
    """
    Activate purchased package (works for both YooKassa and Telegram Stars)

    Args:
        session: Database session
        user: User object
        package: Package configuration dict
        package_type: Package type string

    Returns:
        Success message text
    """
    from bot.database.crud_subscriptions import create_subscription

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

    return success_msg


# ============================================================================
# Legacy handlers (for backward compatibility)
# ============================================================================

@router.callback_query(F.data == "buy_starter")
async def buy_starter_package(callback: CallbackQuery):
    """Purchase Starter package (legacy handler)"""
    await show_payment_methods(callback.__class__(
        **{**callback.__dict__, 'data': 'select_package_starter'}
    ))


@router.callback_query(F.data == "buy_medium")
async def buy_medium_package(callback: CallbackQuery):
    """Purchase Medium package (legacy handler)"""
    await show_payment_methods(callback.__class__(
        **{**callback.__dict__, 'data': 'select_package_medium'}
    ))


@router.callback_query(F.data == "buy_large")
async def buy_large_package(callback: CallbackQuery):
    """Purchase Large package (legacy handler)"""
    await show_payment_methods(callback.__class__(
        **{**callback.__dict__, 'data': 'select_package_large'}
    ))


@router.callback_query(F.data == "buy_subscription_standard")
async def buy_subscription_standard(callback: CallbackQuery):
    """Purchase Standard subscription (legacy handler)"""
    await show_payment_methods(callback.__class__(
        **{**callback.__dict__, 'data': 'select_package_subscription_standard'}
    ))


@router.callback_query(F.data == "buy_subscription_premium")
async def buy_subscription_premium(callback: CallbackQuery):
    """Purchase Premium subscription (legacy handler)"""
    await show_payment_methods(callback.__class__(
        **{**callback.__dict__, 'data': 'select_package_subscription_premium'}
    ))


@router.callback_query(F.data == "subscribe_standard")
async def subscribe_standard(callback: CallbackQuery):
    """Subscribe to Standard plan (legacy handler)"""
    await show_payment_methods(callback.__class__(
        **{**callback.__dict__, 'data': 'select_package_subscription_standard'}
    ))


@router.callback_query(F.data == "subscribe_premium")
async def subscribe_premium(callback: CallbackQuery):
    """Subscribe to Premium plan (legacy handler)"""
    await show_payment_methods(callback.__class__(
        **{**callback.__dict__, 'data': 'select_package_subscription_premium'}
    ))
