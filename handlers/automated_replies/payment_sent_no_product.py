import asyncio
import random
from utils.forward_ticket_to_admin import forward_ticket_to_admin


# TODO: (If user has an order then waits 30 minutes to see if the order has been marked as paid) (+if user hasnt even made an order then tell him to stfu and maybe even put him in restricted)
async def handle_payment_sent_no_product(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await bot.send_message(user_id, "Sometimes it can take up to 30 minutes for the product to arrive after payment")

    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, "Especially with some crypto networks or mercuryo, it can take a bit")

    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, "If you dont get it soon, we will check it from our side and follow up with you")
    await forward_ticket_to_admin(db, bot, user, ticket, lang)
