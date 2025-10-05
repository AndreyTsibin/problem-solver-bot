from datetime import datetime
from typing import Optional, List
from sqlalchemy import BigInteger, Boolean, Integer, String, Text, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class User(Base):
    """User model for storing Telegram user data"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(32))
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(10))  # 'male', 'female'
    birth_date: Mapped[Optional[datetime]] = mapped_column(DateTime)  # Date of birth for age calculation
    occupation: Mapped[Optional[str]] = mapped_column(String(100))  # User's occupation/job
    work_format: Mapped[Optional[str]] = mapped_column(String(20))  # 'remote', 'office', 'hybrid', 'student'
    problems_remaining: Mapped[int] = mapped_column(Integer, default=1)  # Optimized for conversion
    discussion_credits: Mapped[int] = mapped_column(Integer, default=0)
    last_purchased_package: Mapped[Optional[str]] = mapped_column(String(20))  # 'starter', 'medium', 'large'

    # Subscription fields
    subscription_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"))

    # Referral fields
    referred_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    referral_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    referral_credits: Mapped[int] = mapped_column(Integer, default=0)  # Bonus credits from referrals

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    problems: Mapped[List["Problem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="user", foreign_keys=[subscription_id])
    referrals: Mapped[List["Referral"]] = relationship(back_populates="referrer", foreign_keys="Referral.referrer_id", cascade="all, delete-orphan")
    referred_users: Mapped[List["User"]] = relationship(foreign_keys=[referred_by])


class Session(Base):
    """Session model for storing active FSM sessions"""
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("problems.id", ondelete="SET NULL"))
    state: Mapped[str] = mapped_column(String(50), nullable=False)  # 'diagnosis', 'questioning', 'solution'
    methodology: Mapped[Optional[str]] = mapped_column(String(50))  # '5_whys', 'fishbone', 'first_principles'
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    conversation_history: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")


class Problem(Base):
    """Problem model for storing problem analysis records"""
    __tablename__ = "problems"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    problem_type: Mapped[Optional[str]] = mapped_column(String(50))  # 'linear', 'multifactor', 'systemic'
    methodology: Mapped[Optional[str]] = mapped_column(String(50))
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    action_plan: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    status: Mapped[str] = mapped_column(String(20), default='active')  # 'active', 'solved', 'archived'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    solved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="problems")


class Payment(Base):
    """Payment model for storing payment records (YooKassa and Telegram Stars)"""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='RUB')  # RUB for YooKassa, XTR for Telegram Stars
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default='pending')
    telegram_payment_id: Mapped[Optional[str]] = mapped_column(String(255))
    payment_id: Mapped[Optional[str]] = mapped_column(String(255))  # YooKassa payment ID
    package_type: Mapped[Optional[str]] = mapped_column(String(50))  # Package type (starter, medium, large, etc.)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="payments")


class Subscription(Base):
    """Subscription model for recurring monthly subscriptions"""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)  # 'standard', 'premium', 'unlimited'
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # Price in Telegram Stars
    solutions_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    discussion_limit: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default='active')  # 'active', 'cancelled', 'expired'
    next_billing_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="subscription", foreign_keys="User.subscription_id")


class Referral(Base):
    """Referral model for tracking referral program"""
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    referred_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Reward tracking
    reward_given: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_amount: Mapped[int] = mapped_column(Integer, default=0)  # Credits rewarded

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    rewarded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    referrer: Mapped["User"] = relationship(back_populates="referrals", foreign_keys=[referrer_id])
    referred: Mapped["User"] = relationship(foreign_keys=[referred_id])
