import asyncio
import random
from utils.forward_ticket_to_admin import forward_ticket_to_admin

async def handle_not_received_drop(db, bot, user, ticket, lang):
    user_id = user.get("user_id")

    messages = {
        "lv": [
            "Sveiki! Lūdzu, atsūtiet dažas bildes vai īsu video kā pierādījumu.",
            "Ja iespējams, iekļaujiet tuvplānu ar piegādes vietu un tās apkārtni."
        ],
        "ee": [
            "Tere! Palun saatke meile mõned pildid või lühike video tõendina.",
            "Võimaluse korral lisage lähivõte kättetoimetamise kohast ja selle ümbrusest."
        ],
        "ru": [
            "Привет! Пожалуйста, пришлите нам несколько фотографий или короткое видео в качестве доказательства.",
            "Если возможно, включите крупный план места доставки и его окрестностей."
        ],
        "eng": [
            "Hey, please send us some pictures or a short video as proof.",
            "If possible, include a closeup of the drop area and the area around it."
        ]
    }

    # Use English as default if lang not in dict
    selected_messages = messages.get(lang, messages["eng"])

    await bot.send_message(user_id, selected_messages[0])
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, selected_messages[1])

    await forward_ticket_to_admin(db, bot, user, ticket, lang)
