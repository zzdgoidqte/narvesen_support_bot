import asyncio
import random

async def handle_not_received_drop(user_id, bot):
    await bot.send_message(user_id, "Hey, sorry to hear you haven’t received your product yet")

    await asyncio.sleep(random.uniform(6, 12))
    await bot.send_message(user_id, "Could you please send us some pictures or a short video as proof?")

    await asyncio.sleep(random.uniform(6, 12))
    await bot.send_message(user_id, "If possible, include a close-up of the drop area")

    await asyncio.sleep(random.uniform(6, 12))
    await bot.send_message(user_id, "And also some shots of the area around it")

    return True  # Ticket should be created
