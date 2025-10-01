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
    problems_remaining: Mapped[int] = mapped_column(Integer, default=1)
    discussion_credits: Mapped[int] = mapped_column(Integer, default=0)
    last_purchased_package: Mapped[Optional[str]] = mapped_column(String(20))  # 'starter', 'medium', 'large'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    problems: Mapped[List["Problem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")


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
    """Payment model for storing Telegram Stars payment records"""
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='XTR')  # Telegram Stars
    provider: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default='pending')
    telegram_payment_id: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="payments")
