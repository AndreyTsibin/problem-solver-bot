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

    # Add main menu buttons
    builder.button(text="🚀 Решить проблему")
    builder.button(text="📖 История")
    builder.button(text="💳 Премиум")
    builder.button(text="ℹ️ Помощь")

    # Adjust layout: 2 buttons per row
    builder.adjust(2, 2)

    # Create markup with persistent display
    return builder.as_markup(
        resize_keyboard=True,  # Auto-size buttons
        is_persistent=True     # Always visible
    )
