import asyncio
import random
from handlers.bot_workflow.forward_ticket_to_admin import forward_ticket_to_admin
from datetime import datetime, timedelta, timezone
from utils.logger import logger


async def handle_payment_sent_no_product(db, bot, user, ticket, lang):
    try:
        user_id = user.get("user_id")
        user_orders = await db.get_orders_for_user(user_id)

        now_utc = datetime.now(timezone.utc)
        thirty_minutes_ago = now_utc - timedelta(minutes=30)

        # Filter today's orders (UTC)
        todays_orders = [
            order for order in user_orders
            if order['created_at'].astimezone(timezone.utc).date() == now_utc.date()
        ]

        # Check if any order created more than 30 minutes ago
        if any(
            order['created_at'].astimezone(timezone.utc) < thirty_minutes_ago
            for order in todays_orders
        ):
            await forward_ticket_to_admin()
        else:
            # Localized messages grouped by language
            messages = {
                "lv": [
                    "Dažreiz var paiet līdz 30 minūtēm, līdz produkts tiek piegādāts pēc maksājuma veikšanas",
                    "Īpaši, ja maksāts ar dažiem kripto tīkliem vai caur Mercuryo, tas var aizkavēties",
                    "Ja produkts drīz nepienāk, mēs pārbaudīsim to no savas puses un sazināsimies ar tevi"
                ],
                "ee": [
                    "Mõnikord võib toote kohaletoimetamine pärast makset võtta kuni 30 minutit",
                    "Eriti mõne krüptovõrgu või Mercuryo kaudu makstes võib see veidi aega võtta",
                    "Kui sa seda varsti ei saa, kontrollime oma poolelt ja võtame sinuga ühendust"
                ],
                "ru": [
                    "Иногда доставка продукта может занять до 30 минут после оплаты.",
                    "Особенно при оплате через некоторые криптосети или Mercuryo это может занять немного времени",
                    "Если вы не получите его в ближайшее время, мы всё проверим со своей стороны и свяжемся с вами"
                ],
                "eng": [
                    "Sometimes it can take up to 30 minutes for the product to arrive after payment",
                    "Especially with some crypto networks or Mercuryo, it can take a bit",
                    "If you don't get it soon, we will check it from our side and follow up with you"
                ]
            }

            # Select based on language or fallback to English
            selected = messages.get(lang, messages["eng"])

            # Send messages with pauses
            await bot.send_message(user_id, selected[0])
            await asyncio.sleep(random.uniform(4, 6))
            await bot.send_message(user_id, selected[1])
            await asyncio.sleep(random.uniform(4, 6))
            await bot.send_message(user_id, selected[2])

            # Dont close ticket yet
    except Exception as e:
        logger.error(f"Error in handle_payent_sent_no_product: {1}")