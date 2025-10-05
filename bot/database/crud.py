from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Session, Problem, Payment, Subscription, Referral
from typing import Optional, List
from datetime import datetime, timedelta
import secrets


def calculate_age(birth_date: datetime) -> Optional[int]:
    """Calculate age from birth date"""
    if not birth_date:
        return None
    today = datetime.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


# User operations
async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    first_name: str
) -> User:
    """Get existing user or create new one"""
    # Try to find existing user
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Update user info if changed
        user.username = username
        user.first_name = first_name
        await session.commit()
        return user
    
    # Create new user
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def update_user_credits(
    session: AsyncSession,
    user_id: int,
    problems_remaining: Optional[int] = None,
    discussion_credits: Optional[int] = None,
    last_purchased_package: Optional[str] = None
):
    """Update user credits and package info"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        if problems_remaining is not None:
            user.problems_remaining = problems_remaining
        if discussion_credits is not None:
            user.discussion_credits = discussion_credits
        if last_purchased_package is not None:
            user.last_purchased_package = last_purchased_package
        await session.commit()


# Problem operations
async def create_problem(
    session: AsyncSession,
    user_id: int,
    title: str,
    problem_type: Optional[str] = None,
    methodology: Optional[str] = None
) -> Problem:
    """Create new problem"""
    problem = Problem(
        user_id=user_id,
        title=title,
        problem_type=problem_type,
        methodology=methodology
    )
    session.add(problem)
    await session.commit()
    await session.refresh(problem)
    return problem


async def get_user_problems(session: AsyncSession, user_id: int, limit: int = 10) -> List[Problem]:
    """Get user's recent problems"""
    result = await session.execute(
        select(Problem)
        .where(Problem.user_id == user_id)
        .order_by(Problem.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
