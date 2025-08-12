import asyncio
import random

# TODO: (If user has an order then waits 30 minutes to see if the order has been marked as paid) (+if user hasnt even made an order then tell him to stfu and maybe even put him in restricted)
async def handle_payment_sent_no_product(user_id, bot):
    await bot.send_message(user_id, "Thanks for letting us know")

    await asyncio.sleep(random.uniform(5, 10))
    await bot.send_message(user_id, "Just a heads-up - sometimes it can take up to 30 minutes for the product to arrive after payment")

    await asyncio.sleep(random.uniform(5, 10))
    await bot.send_message(user_id, "Especially with some crypto networks, it can take a bit")

    await asyncio.sleep(random.uniform(5, 10))
    await bot.send_message(user_id, "If you don’t get it soon, we’ll check it from our side and follow up with you")

    return True  # Ticket should be created