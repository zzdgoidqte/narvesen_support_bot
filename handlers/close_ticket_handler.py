from aiogram import Router
from aiogram.types import CallbackQuery
from controllers.db_controller import DatabaseController
from keyboards.inline import ticket_closed

router = Router()

@router.callback_query(lambda c: c.data.startswith("close_ticket:"))
async def close_ticket_callback(callback: CallbackQuery, db: DatabaseController):
    ticket_id = callback.data.split(":")[1]
    text = "✅ TICKET CLOSED ✅ \n\nℹ️ You can't chat with the client until this bot sends another ticket from him!\nℹ️ Write him a private message from your account if you need to talk to him."

    # Edit the CLOSE TICKET button
    await callback.message.edit_reply_markup(reply_markup=ticket_closed())

    # Close in DB
    await db.close_support_ticket(int(ticket_id))

    # Notify user
    await callback.message.answer(text)

