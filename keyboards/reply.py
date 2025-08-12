from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def start_kb() -> ReplyKeyboardMarkup:
    """
    Builds a reply keyboard for the /start command using ReplyKeyboardBuilder.

    Returns:
        ReplyKeyboardMarkup: The constructed keyboard.
    """
    builder = ReplyKeyboardBuilder()

    # Add buttons to the keyboard
    builder.button(text="/start")

    # Return the markup with resize and one-time options
    return builder.as_markup(
        resize_keyboard=True,  # Adjusts keyboard size to fit screen
        one_time_keyboard=True,  # Hides keyboard after one use (optional)
    )

