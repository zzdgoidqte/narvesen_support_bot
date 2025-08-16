import asyncio
import random

async def handle_check_product_availability(db, bot, user, ticket, lang):
    await db.close_support_ticket(ticket.get('ticket_id'))

    bot_settings = await db.get_bot_settings()
    bot_username = bot_settings.get('bot_username', 'narvesen247')
    user_id = user.get("user_id")

    message_variations = {
        "lv": [
            [
                f"Ja @{bot_username} rāda produktu un vēlamo daudzumu izvēlētajā vietā, tad tas ir pieejams.", 
                "Ja tas nav pieejams, mēs darām visu iespējamo, lai to pēc iespējas ātrāk papildinātu."
            ]
        ],
        "ee": [
            [
                f"Kui @{bot_username} kuvab sinu soovitud toote ja koguse valitud asukohas, siis on see saadaval.",
                "Kui see pole saadaval, teeme kõik endast oleneva, et see võimalikult kiiresti uuesti laos oleks."
            ]
        ],
        "ru": [
            [
                f"Если @{bot_username} показывает нужный товар и нужное количество в выбранной локации, значит он доступен.", 
                "Если его нет в наличии, мы делаем всё возможное, чтобы как можно скорее пополнить запасы."
            ]
        ],
        "eng": [
            [
                f"If @{bot_username} lists the product and amount you wish to buy at your desired location, then it is available.", 
                "If it’s not available, we are doing our best to restock it as soon as possible."
            ]
        ]
    }

    selected_messages = random.choice(message_variations.get(lang, message_variations["eng"]))

    await bot.send_message(user_id, selected_messages[0])
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, selected_messages[1])
