import asyncio
import random
from utils.forward_ticket_to_admin import forward_ticket_to_admin


async def handle_voice_message(user_id, bot):
    await bot.send_message(user_id, "Can you please send text instead of a voice message?")
    await asyncio.sleep(random.uniform(6, 12))
    await bot.send_message(user_id, "My phones audio doesn't work")

    return False # No ticket needed

async def handle_prompt_for_issue(user_id, bot):
    await bot.send_message(user_id, "Hi, You need help with anything?")

    return False # No ticket needed
    
async def handle_thanks(user_id, bot):
    await bot.send_message(user_id, "👍")

    return False # No ticket needed

async def handle_forward_to_admin(user_id, bot):
    return True  # Ticket should be created
