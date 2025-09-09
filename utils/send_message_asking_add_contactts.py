import os
import json
import asyncio
import random
from telethon import TelegramClient
from telethon.errors import RPCError
from utils.helpers import get_socks5_sticky_proxy

greetings = [
    "yooooooo",
    "sup bro",
    "yo add me fr",
    "heyyyyy u there?",
    "aight let’s gooo",
    "че как, добавь",
    "бро, закинь в контакты",
    "эй, чё как, добавь меня",
    "yo slide me in the contacts",
    "давай в тг добавь"
]

## manually send message to support admin who will add to contacts. essential for new sessions so they can make groups together
async def rename_and_send_from_all_sessions(session_dir: str, target_username="@NarvesenSupport"):
    session_files = [f for f in os.listdir(session_dir) if f.endswith(".session")]
    for session_file in session_files:
        session_name = session_file.replace(".session", "")
        session_path = os.path.join(session_dir, session_name)
        json_path = os.path.join(session_dir, session_name + ".json")

        # Load API credentials
        try:
            with open(json_path, "r") as f:
                creds = json.load(f)
                api_id = creds.get("app_id")
                api_hash = creds.get("app_hash")
                if not api_id or not api_hash:
                    print(f"[{session_name}] Missing credentials.")
                    continue
        except Exception as e:
            print(f"[{session_name}] Error loading JSON: {e}")
            continue

        # Get SOCKS5 proxy
        proxy = get_socks5_sticky_proxy(session_name)
        if not proxy:
            print(f"[{session_name}] Failed to retrieve proxy.")
            continue
        time = random.randint(14, 35)
        await asyncio.sleep(time)
        # Start Telegram client
        client = TelegramClient(session_path, api_id, api_hash, proxy=proxy)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"[{session_name}] Not authorized. Skipping.")
                await client.disconnect()
                continue

            # Send message
            try:
                message_text = random.choice(greetings)
                await client.send_message(target_username, message_text)
                print(f"[{session_name}] Sent message to {target_username}")
            except RPCError as e:
                print(f"[{session_name}] Failed to send message: {e}")

            await client.disconnect()

        except Exception as e:
            print(f"[{session_name}] General error: {e}")
            await client.disconnect()



# Entry point
if __name__ == "__main__":
    async def main():
        await rename_and_send_from_all_sessions('sessions/narvesensupportbot')

    asyncio.run(main())