import asyncio
import random

async def handle_product_arrival_time(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await db.close_support_ticket(ticket.get('ticket_id'))

    messages = {
    "lv": """Piegādes laiks pēc maksājuma:

TRX / USDT / ETH: līdz 3 min  
Litecoin / Karte: 5-15 min  
Bitcoin: 10-60 min

⏳ Apmaksa var dažkārt aizņemt ilgāku laiku. Ja gaidi pārāk ilgi, sazinies ar mums vēlreiz.

🔒 Ja maksā ar karti caur Mercuryo: tā nav mūsu platforma, un mēs neesam atbildīgi par viņu sistēmas aizkavēm vai problēmām. Ja rodas kādas problēmas, lūdzu, sazinies ar Mercuryo atbalstu, nevis ar mums.""",

    "ee": """Kohaletoimetamise aeg pärast makset:

TRX / USDT / ETH: kuni 3 min  
Litecoin / Kaart: 5-15 min  
Bitcoin: 10-60 min

⏳ Mõnikord võib makse töötlemine võtta kauem aega. Kui ootad liiga kaua, võta meiega uuesti ühendust.

🔒 Kui maksad kaardiga läbi Mercuryo: see ei ole meie platvorm ja me ei vastuta nende viivituste ega probleemide eest. Probleemide korral võta ühendust Mercuryo klienditoega, mitte meiega.""",

    "ru": """Время доставки после оплаты:

TRX / USDT / ETH: до 3 мин  
Litecoin / Карта: 5-15 мин  
Bitcoin: 10-60 мин

⏳ Иногда обработка платежа может занять больше времени. Если вы ждёте слишком долго - напишите нам снова.

🔒 При оплате картой через Mercuryo: это не наша платформа, и мы не несем ответственности за её задержки или ошибки. В случае проблем обращайтесь в поддержку Mercuryo, а не к нам.""",

    "eng": """Delivery time after payment:

TRX / USDT / ETH: up to 3 min  
Litecoin / Card: 5–15 min  
Bitcoin: 10–60 min

⏳ Payment processing could sometimes take longer. Contact us again if you're waiting too long.

🔒 If paying by card via Mercuryo: it's not our platform and we are not responsible for their delays or issues. If something goes wrong, please contact Mercuryo support, not us."""
}


    message_text = messages.get(lang, messages["eng"])

    await bot.send_message(user_id, message_text)
