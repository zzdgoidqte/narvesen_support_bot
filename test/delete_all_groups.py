from telethon import TelegramClient
from telethon.tl.functions.channels import DeleteChannelRequest
from telethon.tl.functions.messages import DeleteChatRequest
from telethon.tl.types import Channel, Chat
import asyncio

# Your API credentials
api_id = 890254  # Replace with your API ID
api_hash = 'c7f054a4d5bd7723edafb0841246bdc8'  # Replace with your API hash
phone = 'sessions/narvesensupportbot/+15876662080.session'  # Replace with your phone number (e.g., +1234567890)

# Initialize the client
client = TelegramClient(phone, api_id, api_hash)

async def delete_all_owned_chats():
    # Get all dialogs (includes groups, supergroups, and channels)
    dialogs = await client.get_dialogs()
    
    for dialog in dialogs:
        entity = dialog.entity
        # Check if the entity is a group, supergroup, or channel and you are the creator
        if (isinstance(entity, (Channel, Chat)) and getattr(entity, 'creator', False)):
            try:
                if isinstance(entity, Channel):
                    # Delete supergroup or channel
                    await client(DeleteChannelRequest(entity))
                    print(f"Deleted supergroup/channel: {entity.title}")
                elif isinstance(entity, Chat):
                    # Delete basic group
                    await client(DeleteChatRequest(entity.id))
                    print(f"Deleted basic group: {entity.title}")
                # Add delay to avoid flood limits
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to delete {entity.title}: {e}")
    
    print("Finished checking and deleting all owned chats.")

# Run the client
with client:
    client.loop.run_until_complete(delete_all_owned_chats())