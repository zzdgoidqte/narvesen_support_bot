import asyncio
import random

async def handle_product_arrival_time(db, bot, user, ticket):
    user_id = user.get("user_id")
    await db.close_support_ticket(ticket.get('ticket_id'))
    await bot.send_message(user_id, "TRX/USDT/ETH up to 3 min.\nLitecoin/Card 5-15 min\nBitcoin 10-60 min\n")

