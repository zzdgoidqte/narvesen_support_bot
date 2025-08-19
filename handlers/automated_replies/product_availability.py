import asyncio
import random
from utils.helpers import query_nano_gpt

async def handle_check_product_availability(db, bot, user, ticket, lang):
    await db.close_support_ticket(ticket.get('ticket_id'))

    bot_settings = await db.get_bot_settings()
    bot_username = bot_settings.get('bot_username', 'narvesen247')
    user_id = user.get("user_id")

    # Original messages (Latvian)
    message1_lv = f"Ja @{bot_username} rāda produktu un vēlamo daudzumu izvēlētajā lokācijā, tad tas ir pieejams"
    message2_lv = "Ja tas nav pieejams, mēs darām visu iespējamo, lai to pēc iespējas ātrāk papildinātu"

    # Normalize language
    target_lang = lang if lang in ["lv", "ee", "ru", "eng"] else "eng"

    # Build prompt for GPT
    prompt = f"""
You are a translation and localization assistant.

Translate the following two Latvian messages to "{target_lang}". Then, rewrite both messages so they convey the same meaning in different words (paraphrase).

Return exactly 2 lines separated only by line breaks (\\n) No extra text or explanation.

Message 1:
\"\"\"{message1_lv}\"\"\"

Message 2:
\"\"\"{message2_lv}\"\"\"
"""

    # Ask AI to handle both messages
    ai_response = await query_nano_gpt(prompt, max_tokens=250)

    if ai_response:
        ai_response = ai_response.replace("\\n", "\n")
        lines = ai_response.strip().split("\n")
        if len(lines) >= 2:
            msg1, msg2 = lines[0].strip(), lines[1].strip()
        else:
            msg1 = message1_lv
            msg2 = message2_lv
    else:
        # Fallback hardcoded messages
        fallback_messages = {
            "lv": [message1_lv, message2_lv],
            "ee": [
                f"Kui @{bot_username} kuvab sinu soovitud toote ja koguse valitud asukohas, siis on see saadaval",
                "Kui see pole saadaval, teeme kõik endast oleneva, et see võimalikult kiiresti uuesti laos oleks"
            ],
            "ru": [
                f"Если @{bot_username} показывает нужный товар и нужное количество в выбранной локации, значит он доступен",
                "Если его нет в наличии, мы делаем всё возможное, чтобы как можно скорее пополнить запасы"
            ],
            "eng": [
                f"If @{bot_username} lists the product and amount you wish to buy at your desired location, then it is available",
                "If it’s not available, we are doing our best to restock it as soon as possible"
            ]
        }

        msg1, msg2 = fallback_messages.get(target_lang, fallback_messages["eng"])

    # Send both messages with a delay
    await bot.send_message(user_id, msg1)
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, msg2)
