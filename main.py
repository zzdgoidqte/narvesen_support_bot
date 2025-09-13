import asyncio
from telethon import events
from telethon.tl.types import User

from workflow.handle_unforwarded_tickets import handle_unforwarded_tickets
from controllers.db_controller import DatabaseController
from utils.telegram_helpers import retrieve_session, get_message_content
from utils.logger import logger

@events.register(events.NewMessage(incoming=True))
async def handle_new_message(event):
    if not event.is_private:
        return

    sender = await event.get_sender()
    if isinstance(sender, User) and not sender.bot:
        print(f"\n📨 New message from {sender.first_name or 'Unknown'} (@{sender.username}):\n{event.message.text}")
        message_type = get_message_content(event.message)

        await db.save_user_message(
            user_id=sender.id,
            message_id=event.message.id,
            user_text=event.message.text,
            message_type=message_type
        )

@events.register(events.MessageEdited(incoming=True))
async def handle_edited_message(event):
    if not event.is_private:
        return

    sender = await event.get_sender()
    if isinstance(sender, User) and not sender.bot:
        print(f"✏️ Edited message from {sender.first_name}:\n{event.message.text}")
        await db.update_edited_message(sender.id, event.message.id, event.message.text)

@events.register(events.MessageDeleted())
async def handle_deleted_message(event):
    if event.is_channel or event.is_group:
        return

    for msg_id in event.deleted_ids:
        print(f"❌ Message ID {msg_id} deleted, but chat info is not available.")


async def main():
    global db
    global client

    db = await DatabaseController(bot=None).initialize()

    client = await retrieve_session('573242089095') # TODO problem with proxy? if connect to proxy then session stops orking??
    if not client:
        logger.error("❌ Failed to retrieve and authorize Telegram client session.")
        return
    
    # Register handlers
    client.add_event_handler(handle_new_message, events.NewMessage(incoming=True))
    client.add_event_handler(handle_edited_message, events.MessageEdited(incoming=True))
    client.add_event_handler(handle_deleted_message)

    logger.info("✅ Client initialized. Starting...")

    try:
        await client.run_until_disconnected()
    except Exception as e:
        logger.exception("❌ Error in main loop", exc_info=e)
    finally:
        if db:
            await db.close()
            logger.info("Database closed.")
        if client:
            await client.disconnect()
            logger.info("Telegram client disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
