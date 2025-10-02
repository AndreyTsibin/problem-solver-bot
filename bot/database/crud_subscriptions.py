"""CRUD operations for subscriptions and referrals"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Subscription, Referral
from typing import Optional
from datetime import datetime, timedelta
import secrets
import string


# Subscription operations
async def create_subscription(
    session: AsyncSession,
    user_id: int,
    plan: str,
    price: int,
    solutions_per_month: int,
    discussion_limit: int
) -> Subscription:
    """Create new subscription for user"""
    subscription = Subscription(
        plan=plan,
        price=price,
        solutions_per_month=solutions_per_month,
        discussion_limit=discussion_limit,
        status='active',
        next_billing_date=datetime.utcnow() + timedelta(days=30)
    )
    session.add(subscription)
    await session.flush()  # Get subscription ID

    # Update user's subscription_id
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.subscription_id = subscription.id
        # Reset monthly solutions
        user.problems_remaining += solutions_per_month

    await session.commit()
    await session.refresh(subscription)
    return subscription


async def get_active_subscription(session: AsyncSession, user_id: int) -> Optional[Subscription]:
    """Get user's active subscription"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.subscription_id:
        return None

    result = await session.execute(
        select(Subscription).where(
            Subscription.id == user.subscription_id,
            Subscription.status == 'active'
        )
    )
    return result.scalar_one_or_none()


async def cancel_subscription(session: AsyncSession, subscription_id: int):
    """Cancel subscription"""
    result = await session.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if subscription:
        subscription.status = 'cancelled'
        subscription.cancelled_at = datetime.utcnow()
        await session.commit()


async def renew_subscription(session: AsyncSession, subscription_id: int, user_id: int):
    """Renew subscription for next month"""
    result = await session.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        return

    # Extend billing date
    subscription.next_billing_date = datetime.utcnow() + timedelta(days=30)

    # Reset user's monthly solutions
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.problems_remaining += subscription.solutions_per_month

    await session.commit()


# Referral operations
def generate_referral_code() -> str:
    """Generate unique referral code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


async def create_referral_code(session: AsyncSession, user_id: int) -> str:
    """Create or get referral code for user"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    if user.referral_code:
        return user.referral_code

    # Generate unique code
    while True:
        code = generate_referral_code()
        # Check if code already exists
        existing = await session.execute(
            select(User).where(User.referral_code == code)
        )
        if not existing.scalar_one_or_none():
            break

    user.referral_code = code
    await session.commit()
    return code


async def get_user_by_referral_code(session: AsyncSession, referral_code: str) -> Optional[User]:
    """Get user by referral code"""
    result = await session.execute(
        select(User).where(User.referral_code == referral_code)
    )
    return result.scalar_one_or_none()


async def create_referral(
    session: AsyncSession,
    referrer_id: int,
    referred_id: int
) -> Referral:
    """Create referral record and grant rewards"""
    # Create referral record
    referral = Referral(
        referrer_id=referrer_id,
        referred_id=referred_id,
        reward_given=True,
        reward_amount=1,  # 1 free solution
        rewarded_at=datetime.utcnow()
    )
    session.add(referral)

    # Grant rewards to both users
    # Referrer gets 1 solution
    result = await session.execute(
        select(User).where(User.id == referrer_id)
    )
    referrer = result.scalar_one_or_none()
    if referrer:
        referrer.referral_credits += 1
        referrer.problems_remaining += 1

    # Referred user gets 1 solution (already has 1 free, total 2)
    result = await session.execute(
        select(User).where(User.id == referred_id)
    )
    referred = result.scalar_one_or_none()
    if referred:
        referred.problems_remaining += 1

    await session.commit()
    await session.refresh(referral)
    return referral


async def get_referral_stats(session: AsyncSession, user_id: int) -> dict:
    """Get user's referral statistics"""
    result = await session.execute(
        select(Referral).where(Referral.referrer_id == user_id)
    )
    referrals = result.scalars().all()

    return {
        'total_referrals': len(referrals),
        'total_rewards': sum(r.reward_amount for r in referrals),
        'recent_referrals': referrals[-5:] if len(referrals) > 5 else referrals
    }


async def get_discussion_limit(session: AsyncSession, user_id: int) -> int:
    """Get user's discussion question limit based on subscription/package"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        return 5  # Default free tier limit

    # Check if user has active subscription
    if user.subscription_id:
        subscription = await get_active_subscription(session, user_id)
        if subscription:
            return subscription.discussion_limit

    # Check package limits
    from bot.config import (
        FREE_DISCUSSION_QUESTIONS,
        STARTER_DISCUSSION_LIMIT,
        MEDIUM_DISCUSSION_LIMIT,
        LARGE_DISCUSSION_LIMIT
    )

    package_limits = {
        'starter': STARTER_DISCUSSION_LIMIT,
        'medium': MEDIUM_DISCUSSION_LIMIT,
        'large': LARGE_DISCUSSION_LIMIT
    }

    return package_limits.get(user.last_purchased_package, FREE_DISCUSSION_QUESTIONS)
