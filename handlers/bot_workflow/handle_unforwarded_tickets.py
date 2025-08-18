import asyncio
import emoji
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from datetime import datetime, timedelta, timezone
from utils.logger import logger
from utils.helpers import query_nano_gpt
from handlers.bot_workflow.forward_ticket_to_admin import forward_ticket_to_admin
from controllers.db_controller import DatabaseController
from handlers.automated_replies import *


USER_CONVERSATIONS = {
    # AI gathers more info, then forwards to admin
    "cant_find_product_or_drop_or_dead_drop": handle_not_received_drop,

    # Automated response
    "dont_know_how_to_pay": handle_payment_help,
    "restock_request_for_product_or_location": handle_restock_info,
    "is_product_still_available": handle_check_product_availability,
    "what_is_usual_product_arrival_time": handle_product_arrival_time, 

    # "👍"
    "user_says_thanks": handle_thanks,
    "issue_resolved_by_user": handle_thanks,
    "ok": handle_thanks,

    # Forward to admin
    "wrong_drop_info": forward_ticket_to_admin,
    "payment_sent_no_product": forward_ticket_to_admin,
    "less_product_received_than_expected": forward_ticket_to_admin, # Maybe automated response?
    "kladmen_or_packaging_complaint": forward_ticket_to_admin, # Maybe automated response?
    "opinion_or_info_question": forward_ticket_to_admin,
    "other": forward_ticket_to_admin,
}

LANGUAGES = ['lv', 'eng', 'ru', 'ee']

async def handle_unforwarded_tickets(db: DatabaseController, bot: Bot):
    """
    Periodically checks for unclosed and unforwardeed tickets (not forwarded to admin for further processing).
    For each one, runs a separate task to handle it.

    If ticket uncategorised (support_issue=None) then categorise the issue.
    Else retrieve additional info from user to complete ticket.
    """
    while True:
        try:
            active_unforwarded_tickets = await db.get_active_support_tickets(messages_forwarded=False)

            for ticket in active_unforwarded_tickets:
                ticket_id = ticket.get("ticket_id")
                messages = ticket.get("messages", [])
                support_issue = ticket.get("support_issue")

                messages.sort(key=lambda msg: msg["message_id"])

                # Skip if user hasn't replied
                last_msg = messages[-1]
                last_msg_time = last_msg.get("created_at") # UTC
                time_diff = datetime.now(timezone.utc) - last_msg_time
                if last_msg.get("replied"): 
                    # Close inactive tickets older than 2 days (if not forwarded to admin)
                    if time_diff > timedelta(days=2):
                        await db.close_support_ticket(ticket_id)
                    continue

                # Reply to user if his latest message was more than 2 minutes ago
                if time_diff > timedelta(seconds=20): # Placeholer 20sec for testing
                    # Mark as handled
                    await db.mark_messages_as_replied(ticket_id)
                    if not support_issue:
                        asyncio.create_task(categorise_ticket(db, bot, ticket))
                    else:
                        asyncio.create_task(handle_categorised_ticket(db, bot, ticket))

            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Error in handle_unforwarded_tickets: {e}")

async def categorise_ticket(db: DatabaseController, bot: Bot, ticket):
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
            # await forward_ticket_to_admin(db, bot, user, ticket, lang)
            return

        # Special media-only cases
        if all(msg in ["(photo)", "(video)", "(video_note)"] for msg in unread_messages):
            category_key = 'media'
            lang = 'other'
            await db.set_lang_and_category_for_ticket(category_key, lang, ticket.get('ticket_id'))
            await forward_ticket_to_admin(db, bot, user, ticket, lang)
            return
        elif all(msg == "(voice)" for msg in unread_messages):
            category_key = 'voice_message'
            lang = 'other'
            await db.set_lang_and_category_for_ticket(category_key, lang, ticket.get('ticket_id'))
            await handle_voice_message(db, bot, user, ticket, lang)
            return
        elif all(is_emoji_only(msg) or msg == '(sticker)' for msg in unread_messages):
            await db.close_support_ticket(ticket.get('ticket_id'))
            return

        # Use Nano-GPT to classify the issue
        input_text = "\n".join(unread_messages)
        prompt = f"""
Classify the following user messages into:

1. One of the following **categories**:
\"\"\"{"\n".join(USER_CONVERSATIONS.keys())}\"\"\"

2. One of the following **languages**:
lv, eng, ru, ee

If you are not more than 80% confident about either the category or the language, use 'other'.

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
            await bot.send_message(user_id, f"LOGGING\nDetected category: {category_key}\nLanguage: {lang}")
            await db.set_lang_and_category_for_ticket(category_key, lang, ticket.get('ticket_id'))
            if category_key == "cant_find_product_or_drop_or_dead_drop": # Lost drop with proof
                if any(msg in ["(photo)", "(video)", "(video_note)"] for msg in unread_messages):
                    await forward_ticket_to_admin(db, bot, user, ticket, lang)
                    return
            await handler_func(db, bot, user, ticket, lang)

    except Exception as e:
        logger.error(f"Error in categorise_ticket: {e}")


async def handle_categorised_ticket(db: DatabaseController, bot: Bot, ticket):
    """
    For now only 1 problems to handle in this scenario 
    1. cant_find_product_or_drop_or_dead_drop

    Before handling these, nano-gpt checks if user has is still complaining or user_says_thanks or issue_resolved_by_user
    
    """
    try:
        user_id = ticket.get("user_id")
        user = await db.get_user_by_id(user_id)
        messages = ticket.get("messages", [])
        support_issue = ticket.get("support_issue")
        lang = ticket.get("lang")
        all_messages = []


        if support_issue not in ["cant_find_product_or_drop_or_dead_drop"]:
            logger.error(f"Error in handle_categorised_task - wrong support issue: {support_issue}")
            return
        
        unread_messages = []
        read_messages = []

        for msg in messages:
            msg_text = msg.get("user_text")

            if await is_message_deleted(bot, user_id, msg.get("message_id")):
                await db.mark_message_as_deleted(msg.get("id"))
                continue

            if not msg.get("replied", False):
                unread_messages.append(msg_text)
            else:
                read_messages.append(msg_text)
            all_messages.append(msg_text)

        if not unread_messages:
            return  # Nothing to respond to

        if len(all_messages) > 50: # Block if spam?
            await db.set_messages_forwarded_for_ticket(ticket.get('ticket_id'))
            await db.mute_user(user_id)
            # await forward_ticket_to_admin(db, bot, user, ticket, lang)
            return
        

        message_variations_courier = {
            "lv": "Mēs sazināsimies ar kurjeriem un visu pārbaudīsim -drīzumā atgriezīsimies ar atbildi.",
            "ee": "Võtame ühendust kulleritega ja kontrollime kõike üle -anname peagi teada.",
            "ru": "Мы свяжемся с курьерами и всё проверим — скоро дадим ответ.",
            "eng": "We will check in with our couriers and review everything — we’ll get back to you shortly."
        }
        if support_issue == "cant_find_product_or_drop_or_dead_drop" and any(
            msg in ["(photo)", "(video)", "(video_note)"] for msg in all_messages
        ):
            message_main = message_variations_courier.get(lang, message_variations_courier["eng"])
            await bot.send_message(user_id, message_main)

            # Check Helsinki time
            helsinki_time = datetime.now(pytz.timezone("Europe/Helsinki"))
            hour = helsinki_time.hour

            if hour >= 22 or hour < 7:
                message_time = get_time_based_message(lang, hour)
                await bot.send_message(user_id, message_time)

            await forward_ticket_to_admin(db, bot, user, ticket, lang)
            return


        input_text = "\n".join(unread_messages)
        prompt = f"""
You are a message classifier.

Classify the following user messages as either:

- "Complaint" → if the user is reporting a problem, expressing frustration, or asking for help.
- "Resolved" → if the user says the issue is fixed, found the answer themselves, or is thanking you.

If unsure about the intent or language, default to "Complaint".

User messages:
\"\"\"{input_text}\"\"\"

Respond with only one word: Complaint or Resolved.
"""

        message_classification = await query_nano_gpt(prompt)
        
        if message_classification.strip().lower() == 'complaint':
            if support_issue == "cant_find_product_or_drop_or_dead_drop":
                message_main = message_variations_courier.get(lang, message_variations_courier["eng"])
                await bot.send_message(user_id, message_main)

                # Check Helsinki time
                helsinki_time = datetime.now(pytz.timezone("Europe/Helsinki"))
                hour = helsinki_time.hour

                if hour >= 22 or hour < 7:
                    message_time = get_time_based_message(lang, hour)
                    await bot.send_message(user_id, message_time)

                await forward_ticket_to_admin(db, bot, user, ticket, lang)
        elif message_classification.strip().lower() == 'resolved':
            await handle_thanks(db, bot, user, ticket, lang)

    except Exception as e:
        logger.error(f"Error in handle_categorised_ticket: {e}")


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
        

def is_emoji_only(text: str) -> bool:
    return all(char in emoji.EMOJI_DATA for char in text if not char.isspace())

from datetime import datetime
import pytz

def get_time_based_message(lang: str, hour: int) -> str:
    is_late = 22 <= hour <= 23
    is_early = 0 <= hour < 7

    if lang == "lv":
        return (
            "Ņemot vērā, ka ir ļoti vēls, šobrīd nevaram garantēt tūlītēju risinājumu." if is_late else
            "Ņemot vērā, ka ir ļoti agrs rīts, šobrīd nevaram garantēt tūlītēju risinājumu."
        )
    elif lang == "ee":
        return (
            "Kuna on väga hiline aeg, ei saa me praegu lahendust garanteerida." if is_late else
            "Kuna on väga varajane hommik, ei saa me praegu lahendust garanteerida."
        )
    elif lang == "ru":
        return (
            "Сейчас очень поздно, поэтому мы не можем гарантировать быстрое решение." if is_late else
            "Сейчас очень рано утром, поэтому мы не можем гарантировать быстрое решение."
        )
    else:  # eng or fallback
        return (
            "Since it is very late, we can't guarantee to resolve the issue right now." if is_late else
            "Since it is very early in the morning, we can't guarantee to resolve the issue right now."
        )
