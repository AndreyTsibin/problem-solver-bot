from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Session, Problem, Payment
from typing import Optional, List


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


async def update_user_premium(session: AsyncSession, user_id: int, is_premium: bool):
    """Update user premium status"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.is_premium = is_premium
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
