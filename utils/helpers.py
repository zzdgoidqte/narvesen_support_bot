import difflib
import aiohttp
import socks
import requests
import os
import random
import json
from telethon import TelegramClient
from urllib.parse import unquote
from config.config import Config
from utils.logger import logger
from controllers.db_controller import DatabaseController



async def query_nano_gpt(prompt: str, model: str = "gpt-5-mini", temperature: float = 0.0, max_tokens: int = 1000) -> str | None:
    """
    Sends a prompt to the Nano-GPT API and returns the model's response.

    Args:
        prompt (str): The prompt to send.
        model (str): The model to use. Default is 'gpt-5-mini'. (gpt-4o-mini and yi-lightning was not as percise in my tests)
        temperature (float): Sampling temperature. (How creative is the model response)
        max_tokens (int): Max tokens to generate. (For simple single sentence output can limit to small amount of tokens)

    Returns:
        str | None: The model's response, or None on failure.
    """
    url = "https://nano-gpt.com/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {Config.NANO_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    json_payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=json_payload) as resp:
                resp.raise_for_status()
                response_json = await resp.json()
                return response_json["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Nano-GPT API request failed: {e}")
        return None

def format_number(value):
    # Remove trailing zeros and decimal point if unnecessary
    return f"{value}".rstrip("0").rstrip(".") if "." in f"{value}" else f"{value}"


def escape_markdown_v1(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV1.
    Escapes '_', '*', '`', '['.

    Args:
        text (str): Text to escape.

    Returns:
        str: Escaped text safe for MarkdownV1.
    """
    special_chars = r"_*[`"
    text = str(text)  # Convert to string to handle non-string inputs
    return "".join(f"\\{char}" if char in special_chars else char for char in text)


def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    Escapes '\', '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'.

    Args:
        text (str): Text to escape.

    Returns:
        str: Escaped text safe for MarkdownV2.
    """
    special_chars = r"\_*[]()~`>#+-=|{}.!"
    text = str(text)  # Convert to string to handle non-string inputs
    return "".join(f"\\{char}" if char in special_chars else char for char in text)


def is_similar_to_start(user_text: str, threshold: float = 0.7) -> bool:
    """
    Check if a message is similar to 'start' using fuzzy matching.
    
    Args:
        user_text (str): The user's message
        threshold (float): Similarity ratio threshold between 0 and 1.

    Returns:
        bool: True if message is similar to 'start'
    """
    if not user_text:
        return False
    user_text = user_text.strip().lower()

    # Remove leading characters like / or #
    cleaned = user_text.lstrip("/#!@$%&*")

    # Compare to 'start'
    similarity = difflib.SequenceMatcher(None, cleaned, "start").ratio()
    return similarity >= threshold

def get_socks5_proxy():
    try:
        url = 'https://ipv4.icanhazip.com'
        proxy = 'geo.iproyal.com:12321'

        # Extract auth credentials
        auth = Config.IPROYAL_PROXY_AUTH  # e.g., 'username:password'
        username, password = auth.split(':')

        # Unquote in case URL encoding is used in credentials
        username = unquote(username)
        password = unquote(password)

        proxies = {
            'http': f'socks5h://{auth}@{proxy}',
            'https': f'socks5h://{auth}@{proxy}'
        }

        # Verify the proxy works and get public IP
        response = requests.get(url, proxies=proxies, timeout=10)
        response.raise_for_status()
        logger.debug(f"Proxy IP: {response.text.strip()}")

        host, port = proxy.split(':')
        return (socks.SOCKS5, host, int(port), True, username, password)

    except Exception as e:
        logger.error(f"Error fetching proxy: {e}")
        return None
    

async def get_random_available_session(db: DatabaseController, group_limit: int = 45) -> TelegramClient:
    """
    Find a usable Telethon session from the directory that owns fewer than `group_limit` groups
    based on the database record (via created_by column). Also updates the first name if needed.
    """
    session_dir = "sessions/narvesensupportbot"
    session_files = [f for f in os.listdir(session_dir) if f.endswith(".session")]
    random.shuffle(session_files)

    for session_file in session_files:
        session_name = session_file.replace(".session", "")
        session_path = os.path.join(session_dir, session_name)
        json_path = os.path.join(session_dir, session_name + ".json")

        # Load API credentials
        try:
            with open(json_path, "r") as f:
                json_data = json.load(f)
                api_id = json_data.get("app_id")
                api_hash = json_data.get("app_hash")
                if not api_id or not api_hash:
                    logger.warning(f"Missing API credentials in {json_path}")
                    continue
        except Exception as e:
            logger.warning(f"Failed to read JSON for session {session_name}: {e}")
            continue

        # Check in DB how many groups this session has created
        try:
            group_count = await db.count_of_groups_created_by(session_name)
            if group_count >= group_limit:
                logger.info(f"Session {session_name} already created {group_count} groups. Skipping.")
                continue
        except Exception as e:
            logger.error(f"Failed to get group count for session {session_name} from DB: {e}")
            continue

        # Initialize and authorize Telethon client
        client = TelegramClient(session_path, api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                logger.warning(f"Session {session_name} is not authorized. Skipping.")
                await client.disconnect()
                continue

            logger.info(f"Using session {session_name} ({group_count} existing groups for this session)")
            return client

        except Exception as e:
            logger.error(f"Failed to initialize or connect session {session_name}: {e}")
            await client.disconnect()
            continue

    logger.error("No available session found.")
    return None
