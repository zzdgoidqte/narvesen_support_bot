import os
import json
from telethon import TelegramClient
from utils.helpers import get_socks5_sticky_proxy, escape_markdown_v1
from utils.logger import logger
from telethon.tl.types import (
    Message,
    MessageMediaPhoto,
    MessageMediaDocument,
    DocumentAttributeVideo,
    DocumentAttributeAudio,
    DocumentAttributeSticker,
    DocumentAttributeAnimated,
    DocumentAttributeFilename
)


async def retrieve_session(session_name):
    session_dir = "sessions/support_bot_admin"
    session_path = os.path.join(session_dir, session_name)
    json_path = os.path.join(session_dir, session_name + ".json")

    if not os.path.exists(json_path):
        logger.warning(f"[Cleanup] JSON file missing for {session_name}")
        return None

    with open(json_path, "r") as f:
        creds = json.load(f)
        api_id = creds.get("app_id")
        api_hash = creds.get("app_hash")

    if not api_id or not api_hash:
        logger.warning(f"[Cleanup] Incomplete credentials for {session_name}")
        return None
    
    proxy = get_socks5_sticky_proxy(session_name)
    if not proxy:
        logger.warning(f"[Cleanup] Unable to retrieve proxy for {session_name}")
        return None

    # Initialize and authorize Telethon client
    try:
        client = TelegramClient(session_path, api_id, api_hash, proxy=proxy)
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(f"[Cleanup] Session {session_name} is not authorized.")
            await client.disconnect()
            return None

        logger.info(f"Using session {session_name}")
        return client
    except Exception as e:
        logger.error(f"[Cleanup] Failed to initialize or connect session {session_name}: {e}")
        if client:
            await client.disconnect()
        return None
    

def get_message_content(message: Message) -> str:
    """Return a label describing the content type of a message (e.g., 'photo', 'video', etc.)"""
    if message.text:
        return 'text'

    media = message.media
    if isinstance(media, MessageMediaPhoto):
        return "photo"

    elif isinstance(media, MessageMediaDocument):
        if not media.document:
            return "document"

        attrs = media.document.attributes
        for attr in attrs:
            if isinstance(attr, DocumentAttributeVideo):
                return "video"
            elif isinstance(attr, DocumentAttributeAudio):
                if getattr(attr, "voice", False):
                    return "voice"
                return "audio"
            elif isinstance(attr, DocumentAttributeSticker):
                return "sticker"
            elif isinstance(attr, DocumentAttributeAnimated):
                return "animation"
            elif isinstance(attr, DocumentAttributeFilename) and attr.file_name.endswith('.ogg'):
                return "voice"

        return "document"

    return "other"