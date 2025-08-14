from utils.forward_ticket_to_admin import forward_ticket_to_admin

async def handle_restock_info(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await db.close_support_ticket(ticket.get('ticket_id'))
    await bot.send_message(user_id, "Currently dont have any info about that, but were trying to restock every product asap")