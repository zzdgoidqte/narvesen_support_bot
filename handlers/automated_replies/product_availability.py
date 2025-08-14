import asyncio
import random
from utils.forward_ticket_to_admin import forward_ticket_to_admin

async def handle_check_product_availability(db, bot, user, ticket):
    await db.close_support_ticket(ticket.get('ticket_id'))
    bot_settings = await db.get_bot_settings()
    bot_username = bot_settings.get('bot_username', 'Narvesen bot')
    await bot.send_message(user_id, f"If {bot_username} lists the product and batch you wish to buy at your desired location, then it is available")
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, f"If its not available then we are doing our best to restock it asap")

    user_id = user.get("user_id")