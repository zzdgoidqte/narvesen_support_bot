from aiogram import Router
from aiogram.types import Message, CallbackQuery


router = Router()

@router.callback_query(lambda c: c.data == "noop")
async def handle_empty_callback(_: CallbackQuery):
    return

# Ensures edited messages are registered in db (so AI can better handle them)
@router.edited_message()
async def handle_edited_message(_: Message):
    pass