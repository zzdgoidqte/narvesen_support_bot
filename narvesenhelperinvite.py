from telethon import TelegramClient
from telethon.errors import RPCError
from config.config import Config  # Assuming your Config class is set up properly
import asyncio

async def send_intro_message():
    api_id = Config.BOT_ADMIN_SESSION_API_ID
    api_hash = Config.BOT_ADMIN_SESSION_API_HASH
    session_path = "sessions/narvesensupportbot/+15876662080.session"

    client = TelegramClient(session_path, api_id, api_hash)

    try:
        await client.start()
        await client.send_message(
            "@NarvesenSupport",
            "Hey, please add me to contacts so I can create groups with you for @NarvesenSupportBot\n\nOnce you've added me, please try using the bot."
        )
        print("Message sent successfully.")

    except RPCError as e:
        print(f"Telegram RPC Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await client.disconnect()

# Run the async function
asyncio.run(send_intro_message())
