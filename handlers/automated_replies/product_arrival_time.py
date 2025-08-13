import asyncio
import random
from utils.forward_ticket_to_admin import forward_ticket_to_admin

async def handle_product_arrival_time(db, bot, user, ticket):
    user_id = user.get("user_id")
    pass