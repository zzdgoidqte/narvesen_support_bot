import asyncio
import random
from aiogram import Router
from utils.forward_ticket_to_admin import forward_ticket_to_admin
 
router = Router()


async def handle_not_received_drop(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await bot.send_message(user_id, "Hey, please send us some pictures or a short video as proof")

    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, "If possible, include a closeup of the drop area and the area around it")
    await forward_ticket_to_admin(db, bot, user, ticket, lang)
