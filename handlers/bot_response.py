import asyncio
import re
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from datetime import datetime, timedelta, timezone
from utils.logger import logger
from utils.helpers import query_nano_gpt
from controllers.db_controller import DatabaseController
from handlers.forward_ticket_to_admin import forward_ticket_to_admin
from handlers.replies import *


USER_CONVERSATIONS = {
    "I haven't received my drop/product/goods": handle_not_received_drop,
    "Payment sent, product not received": handle_payment_sent_no_product,
    "When is restock coming for product/location?": handle_restock_info,
    "Thanks/All good": handle_thanks,
    "Oh nevermind, problem solved, all is good": handle_thanks,
    "I have received incorect drop information or wrong drop": handle_forward_to_admin,
	"Received less product than expected": handle_forward_to_admin,
    "What do you think about ..?": handle_forward_to_admin,
    "Other": handle_forward_to_admin,
    "Spam": handle_spam,
}

async def categorise_problem(db: DatabaseController, bot: Bot):
    """
    Periodically checks for tickets needing categorisation.
    For each one, runs a separate task to handle it.

    Categorizes user response into 'conversation' and 'issue'
    """
    while True:
        try:
            active_tickets = await db.get_support_tickets(exclude_closed=True, exclude_messages_unforwarded=False)

            for ticket in active_tickets:
                ticket_id = ticket.get("ticket_id")
                messages = ticket.get("messages", [])
                messages.sort(key=lambda msg: msg["message_id"])

                # Double check just in case
                if ticket.get("closed"):
                    continue

                # Skip if user hasn't replied
                last_msg = messages[-1]
                last_msg_time = last_msg.get("created_at") # UTC
                time_diff = datetime.now(timezone.utc) - last_msg_time
                if last_msg.get("replied"): 
                    # Close inactive tickets older than 3 days
                    if time_diff > timedelta(days=3):
                        await db.close_support_ticket(ticket_id) 
                    continue

                # Reply to user if his latest message was more than 2 minutes ago
                if time_diff > timedelta(seconds=20):
                    # Mark as handled
                    await db.mark_messages_as_replied(ticket_id)
                    asyncio.create_task(handle_ticket(db, bot, ticket))

            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Error in categorise_problem: {e}")

async def handle_ticket(db: DatabaseController, bot: Bot, ticket):
    try:
        user_id = ticket.get("user_id")
        user = await db.get_user_by_id(user_id)
        messages = ticket.get("messages", [])

        unread_messages = []
        read_messages = []

        for msg in messages:
            msg_text = msg.get("user_text")
            if msg.get("replied"):
                if not msg.get('is_deleted'):
                    read_messages.append(msg_text)
            else:
                if await is_message_deleted(bot, user_id, msg.get('message_id')):
                    await db.mark_message_as_deleted(msg.get('id'))
                    continue
                unread_messages.append(msg_text)

        if not unread_messages:
            return  # Nothing to respond to

        if len(unread_messages) > 50: # Block if spam
            await db.set_messages_forwarded_for_ticket(ticket.get('ticket_id'))
            await forward_ticket_to_admin(db, bot, user, ticket)
            return

        # Special media-only cases
        if all(msg in ["(photo)", "(video)", "(video_note)"] for msg in unread_messages):
            await forward_ticket_to_admin(db, bot, user, ticket)
            return
        elif all(msg == "(voice)" for msg in unread_messages):
            await handle_voice_message(user_id, bot)
            return

        # Use Nano-GPT to classify the issue
        input_text = "\n".join(unread_messages)
        prompt = f"""
    Classify the user's messages into one of: {", ".join(USER_CONVERSATIONS.keys())}

    Messages:
    {input_text}

    Reply with only the matching key.
    """
        
        category_key = await query_nano_gpt(prompt)
        logger.info(f"Detected response category: {category_key}")

        # Check if it's a valid handler key
        handler_func = None
        if category_key in USER_CONVERSATIONS:
            handler_func = USER_CONVERSATIONS[category_key]

        if handler_func:
            should_forward_ticket = await handler_func(user_id, bot)
            if should_forward_ticket:
                await db.set_messages_forwarded_for_ticket(ticket.get('ticket_id'))
                await forward_ticket_to_admin(db, bot, user, ticket)
        else:
            # Unknown or invalid response from model (possible prompt injection)
            logger.warning(f"Unrecognized category from model: {category_key}")
            await db.set_messages_forwarded_for_ticket(ticket.get('ticket_id'))
            await forward_ticket_to_admin(db, bot, user, ticket)

    except Exception as e:
        logger.error(f"Error in handle_ticket: {e}")


async def is_message_deleted(bot: Bot, chat_id: int, message_id: int) -> bool:
    try:
        # Try to copy the message to self to see if it was deleted (only workaround i could find..)
        await bot.copy_message(
            chat_id=1234567890,  # Dummy chat ID
            from_chat_id=chat_id,
            message_id=message_id
        )
        return False  # Message exists
    except TelegramAPIError as e:
        # This could be due to message not found, deleted, or other issues
        error_text = str(e).lower()
        if (
            "message to copy not found" in error_text
            or "message_id_invalid" in error_text
            or "message identifier is not valid" in error_text
        ):
            return True  # Message was deleted or doesn't exist
        elif "chat not found" in error_text:
            return False  # Error about chat_id which means message_id hasnt been deleted
        else:
            logger.error(f"Error in is_message_deleted: {e}")
            return False