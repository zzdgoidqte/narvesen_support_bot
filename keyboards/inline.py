from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def payment_help_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🆘 Payment Problems? 🆘", callback_data="payment_help"))
    return builder.as_markup()

def close_ticket(ticket_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Close Ticket 📝", callback_data=f"close_ticket:{ticket_id}"))
    return builder.as_markup()

def ticket_closed() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Edit the inline keyboard to disable the button
    builder.row(InlineKeyboardButton(text="✅ CLOSED ✅", callback_data="noop"))
    return builder.as_markup()
