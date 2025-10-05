"""Persistent keyboard module for bot UI"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create persistent main menu keyboard with simplified 2-button layout.

    Returns:
        ReplyKeyboardMarkup with buttons for main actions
    """
    builder = ReplyKeyboardBuilder()

    # Simplified menu: only 2 buttons
    builder.button(text="🚀 Решить проблему")
    builder.button(text="👤 Профиль")

    # Adjust layout: 2 buttons in one row
    builder.adjust(2)

    # Create markup with persistent display
    return builder.as_markup(
        resize_keyboard=True,        # Auto-size buttons
        is_persistent=True,          # Always visible
        input_field_placeholder=""   # Prevent auto-opening keyboard on mobile
    )
