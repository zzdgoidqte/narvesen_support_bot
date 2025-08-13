from utils.forward_ticket_to_admin import forward_ticket_to_admin

async def handle_restock_info(db, bot, user, ticket):
    user_id = user.get("user_id")
    await bot.send_message(user_id, "Currently dont have any info about that")

    return False # No ticket needed