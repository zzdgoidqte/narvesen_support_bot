import aiohttp
import socks
import emoji
from config.config import Config
from utils.logger import logger


def is_emoji_only(text: str) -> bool:
    return all(char in emoji.EMOJI_DATA for char in text if not char.isspace())

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


def get_socks5_sticky_proxy(session_name: str):
    """
    Generate a SOCKS5 sticky proxy tuple for use with Telethon or similar libraries,
    using IPRoyal's session-based sticky IP format.

    Args:
        session_name (str): A unique identifier (e.g., phone number) to be used
                            as the sticky session name. This name determines which
                            IP is assigned and kept for 168 hours.

    Returns:
        tuple: A tuple formatted as (proxy_type, host, port, rdns, username, password),
               compatible with Telethon.
    """
    try:
        proxy_host = 'geo.iproyal.com'
        proxy_port = 12321

        session_name = session_name.replace("+", "").strip()

        username, base_password = Config.IPROYAL_PROXY_AUTH.split(':')

        full_password = f"{base_password}_session-{session_name}_lifetime-168h"

        return (socks.SOCKS5, proxy_host, proxy_port, True, username, full_password)

    except Exception as e:
        logger.error(f"[Proxy {session_name}] Error: {e}")
        return None

