"""Persistent keyboard module for bot UI"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create persistent main menu keyboard with primary bot functions.

    Returns:
        ReplyKeyboardMarkup with buttons for main actions
    """
    builder = ReplyKeyboardBuilder()

    # Row 1: Main actions
    builder.button(text="🚀 Решить проблему")
    builder.button(text="📖 История")

    # Row 2: Subscriptions and Referrals
    builder.button(text="💎 Подписки")
    builder.button(text="🎁 Рефералы")

    # Adjust layout: 2 buttons per row for all rows
    builder.adjust(2, 2)

    # Create markup with persistent display
    return builder.as_markup(
        resize_keyboard=True,  # Auto-size buttons
        is_persistent=True     # Always visible
    )
