import asyncio
import random

async def handle_product_arrival_time(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await db.close_support_ticket(ticket.get('ticket_id'))

    messages = {
        "lv": "Piegādes laiks pēc maksājuma:\n\nTRX / USDT / ETH: līdz 3 min\nLitecoin / Karte: 5–15 min\nBitcoin: 10–60 min",
        "ee": "Kohaletoimetamise aeg pärast makset:\n\nTRX / USDT / ETH: kuni 3 min\nLitecoin / Kaart: 5–15 min\nBitcoin: 10–60 min",
        "ru": "Время доставки после оплаты:\n\nTRX / USDT / ETH: до 3 мин\nLitecoin / Карта: 5–15 мин\nBitcoin: 10–60 мин",
        "eng": "Delivery time after payment:\n\nTRX / USDT / ETH: up to 3 min\nLitecoin / Card: 5–15 min\nBitcoin: 10–60 min"
    }

    message_text = messages.get(lang, messages["eng"])

    await bot.send_message(user_id, message_text)
