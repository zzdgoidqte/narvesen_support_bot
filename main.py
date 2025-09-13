import asyncio
from telethon import events
from telethon.tl.types import User

from workflow.handle_unforwarded_tickets import handle_unforwarded_tickets
from controllers.db_controller import DatabaseController
from utils.telegram_helpers import retrieve_session, get_message_content
from utils.logger import logger

db = None # define globally so event handler can use it
client = None

@events.register(events.NewMessage(incoming=True))
async def handle_new_message(event):
    if not event.is_private:
        return  # Only handle private messages
    
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
        return  # Only handle private messages
    
    sender = await event.get_sender()
    if isinstance(sender, User) and not sender.bot:
        print(f"✏️ Edited message from {sender.first_name}:\n{event.message.text}")
        await db.update_edited_message(sender.id, event.message.id, event.message.text)

@events.register(events.MessageDeleted())
async def handle_deleted_message(event):
    if not event.is_private:
        return  # Only handle private messages
    
    for msg_id in event.deleted_ids:
        print(f"❌ Message with ID {msg_id} was deleted in chat {event.chat_id}")


async def main():
    global db
    global client
    try:
        # Initialize database
        db = await DatabaseController(bot=None).initialize()
        client = await retrieve_session('573242089095')
        if not client:
            logger.error("❌ Failed to retrieve and authorize Telegram client session.")
            return
        
        # Register event handlers
        client.add_event_handler(handle_new_message)
        client.add_event_handler(handle_edited_message)
        client.add_event_handler(handle_deleted_message)

        # Run the database ticket handler concurrently
        task1 = asyncio.create_task(handle_unforwarded_tickets(db, client))

        # Run the Telegram client (this will block until disconnected)
        task2 = asyncio.create_task(client.run_until_disconnected())

        logger.info("Session is running and listening for new private messages.")

        # Wait for both tasks to complete
        await asyncio.gather(task1, task2)

    except Exception as e:
        logger.exception("Error occurred in main loop:", exc_info=e)

    finally:
        if db:
            await db.close()
            logger.info("Database connection closed.")
        if client:
            await client.disconnect()
            logger.info("Telegram client disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
