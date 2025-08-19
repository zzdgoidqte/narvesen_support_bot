import asyncio
import random

async def handle_voice_message(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await bot.send_message(user_id, "Can you please send text instead of a voice message?")
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, "My phones audio doesn't work")

async def handle_thanks(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await db.close_support_ticket(ticket.get('ticket_id'))
    await bot.send_message(user_id, "👍")
    return