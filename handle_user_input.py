import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from datetime import datetime, timedelta, timezone
from utils.logger import logger
from utils.helpers import query_nano_gpt
from utils.forward_ticket_to_admin import forward_ticket_to_admin
from controllers.db_controller import DatabaseController
from handlers.automated_replies import *


USER_CONVERSATIONS = {
    # AI gathers more info, decides weather to respond or forward to admin 
    "cant_find_product_or_drop_or_dead_drop": handle_not_received_drop, # Gather info, forward to admin
    "payment_sent_no_product": handle_payment_sent_no_product, # Gather info, if order made more than 30 min ago then forward to admin, else tell user to wait
    "dont_know_how_to_pay": handle_payment_help, # Tutorial
    "restock_request_for_product_or_location": handle_restock_info, # Forward to admin? Or auto-reply "idk"
    "is_product_still_available": handle_check_product_availability, # Checks database, automated response
    "what_is_usual_product_arrival_time": handle_product_arrival_time, # AI 

    # "👍"
    "user_says_thanks": handle_thanks,
    "issue_resolved_by_user": handle_thanks,

    # Forward to admin
    "wrong_drop_info": forward_ticket_to_admin,
    "less_product_received_than_expected": forward_ticket_to_admin, # Maybe automated response?
    "kladmen_or_packaging_complaint": forward_ticket_to_admin, # Maybe automated response?
    "opinion_question": forward_ticket_to_admin,
    "other": forward_ticket_to_admin,
}

LANGUAGES = ['lv', 'eng', 'ru', 'ee']

async def handle_user_input(db: DatabaseController, bot: Bot):
    """
    Periodically checks for tickets needing categorisation.
    For each one, runs a separate task to handle it.

    Categorizes user response into 'conversation' and 'issue'
    """
    while True:
        try:
            # Retrieve all active, uncategorised tickets that are not forwarded to admin
            active_tickets = await db.get_support_tickets(exclude_closed=True, exclude_messages_unforwarded=False, exclude_categorised=True)

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
            logger.error(f"Error in handle_user_input: {e}")

async def handle_ticket(db: DatabaseController, bot: Bot, ticket):
    try:
        user_id = ticket.get("user_id")
        user = await db.get_user_by_id(user_id)
        messages = ticket.get("messages", [])

        unread_messages = []

        for msg in messages:
            msg_text = msg.get("user_text")
            if await is_message_deleted(bot, user_id, msg.get('message_id')):
                await db.mark_message_as_deleted(msg.get('id'))
                continue
            unread_messages.append(msg_text)

        if not unread_messages:
            return  # Nothing to respond to

        if len(unread_messages) > 50: # Block if spam?
            await db.set_messages_forwarded_for_ticket(ticket.get('ticket_id'))
            await db.mute_user(user_id)
            await forward_ticket_to_admin(db, bot, user, ticket)
            return

        # Special media-only cases
        if all(msg in ["(photo)", "(video)", "(video_note)"] for msg in unread_messages):
            await forward_ticket_to_admin(db, bot, user, ticket)
            return
        elif all(msg == "(voice)" for msg in unread_messages):
            await handle_voice_message(db, bot, user, ticket)
            return

        # Use Nano-GPT to classify the issue
        input_text = "\n".join(unread_messages)
        prompt = f"""
Classify the following user messages into:

1. One of the following **categories**:
\"\"\"{"\n".join(USER_CONVERSATIONS.keys())}\"\"\"

2. One of the following **languages**:
lv, eng, ru, ee

If you are not confident about either the category or the language, use 'other'.

User messages:
\"\"\"{input_text}\"\"\"

Respond **only** in this format (no extra explanation):
lang:category
"""
        
        lang_and_category_key = await query_nano_gpt(prompt)

        if ':' in lang_and_category_key:
            lang, category_key = lang_and_category_key.strip().split(':', 1)
            # Normalize and validate
            lang = lang.strip().lower()
            category_key = category_key.strip()

            # Handle unexpected output
            category_key = 'other' if category_key not in USER_CONVERSATIONS else category_key
            lang = 'other' if lang not in LANGUAGES else lang

            logger.info(f"Detected language: {lang}")
            logger.info(f"Detected response category: {category_key}")
        else:
            logger.warning(f"Unexpected format from GPT: '{lang_and_category_key}'")
            lang = 'other'
            category_key = 'other'

        # Check if it's a valid handler key
        handler_func = USER_CONVERSATIONS[category_key]

        if handler_func:
            await db.set_lang_and_category_for_ticket(category_key, lang, ticket.get('ticket_id'))
            await handler_func(db, bot, user, ticket)

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