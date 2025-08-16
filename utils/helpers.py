import difflib
import aiohttp
from config.config import Config
from utils.logger import logger



async def query_nano_gpt(prompt: str, model: str = "yi-lightning", temperature: float = 0.0, max_tokens: int = 15) -> str | None:
    """
    Sends a prompt to the Nano-GPT API and returns the model's response.

    Args:
        prompt (str): The prompt to send.
        model (str): The model to use. Default is 'yi-lightning'. (gpt-4o-mini was not as percise in my tests)
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
