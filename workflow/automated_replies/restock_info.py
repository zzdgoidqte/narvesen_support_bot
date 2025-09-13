from utils.helpers import query_nano_gpt

async def handle_restock_info(db, client, user, ticket, lang):
    user_id = user.get("user_id")
    await db.close_support_ticket(ticket.get('ticket_id'))

    # Normalize language
    target_lang = lang if lang in ["lv", "ee", "ru", "eng"] else "eng"

    # Example message
    base_text = (
        "Pašlaik mums nav informācijas par šo preci, bet mēs cenšamies pēc iespējas ātrāk atjaunot krājumus visiem produktiem"
    )

    # Improved prompt
    prompt = f"""
You are a translation and localization assistant. Translate the following Latvian text into "{target_lang}".
After translating it, rephrase the message so that it conveys the same meaning but uses different wording.
Do not provide any explanation - return only the final rephrased translation as a single line of text.

Original text:
\"\"\"{base_text}\"\"\"
"""

    # Query the AI for the translated and rephrased message
    ai_response = await query_nano_gpt(prompt)

    # Send the AI-generated message to the user
    if ai_response:
        message_text = ai_response.strip()
        await client.send_message(user_id, message_text)
    else:
        # Fallback in case AI fails
        fallback_messages = {
            "lv": base_text,
            "ee": "Hetkel pole meil selle toote kohta infot, kuid püüame kõik tooted võimalikult kiiresti laost uuesti kättesaadavaks teha",
            "ru": "Сейчас у нас нет информации об этом товаре, но мы стараемся как можно быстрее пополнить все запасы",
            "eng": "Currently we don’t have any info about that, but we’re trying to restock every product as soon as possible"
        }
        await client.send_message(user_id, fallback_messages.get(target_lang, fallback_messages["eng"]))
