from aiogram import Router, Bot
from aiogram.types import InputMediaPhoto, FSInputFile
from controllers.db_controller import DatabaseController
from utils.forward_ticket_to_admin import forward_ticket_to_admin
import asyncio
import random

router = Router()

async def handle_payment_help(db, bot, user, ticket: Bot, lang):
    await db.close_support_ticket(ticket.get('ticket_id'))
    user_id = user.get("user_id")
    crypto_guide = """
<b>💸 How to Pay with Crypto (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Buy crypto using any wallet - we recommend  <a href="https://www.bybit.com/">Bybit</a>

2. Send the exact amount to the wallet address we give you when you make an order.

<b>⚡ Best Option: LTC or USDT-TRC20</b> — low fees & fast confirmation.

3. Once confirmed, you’ll get your order.
"""

    await bot.send_message(
        user_id,
        crypto_guide,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    photo1 = FSInputFile("data/card_payment_1.jpg")
    photo2 = FSInputFile("data/card_payment_2.jpg")

    media = [
        InputMediaPhoto(
            media=photo1,
            caption="""
<b>💳 How to Pay with Card</b>

1. Copy the wallet address we send.

2. Go to <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Pick LTC, paste the LTC amount under "You get", click buy. Then paste in the wallet address. Then enter your card details and pay.

✅ Once we get the crypto, your order is sent.

<b>🔒 Note:</b> We don’t own Mercuryo - your info stays private.

⚠️ Exchange fees apply. Crypto payments are cheaper & faster!
""",
            parse_mode="HTML"
        ),
        InputMediaPhoto(media=photo2)
    ]
    await bot.send_media_group(user_id, media)

    warning_msg = """
<b>‼️ Important Before You Pay ‼️</b>

Some crypto like BTC can be slow when the network is busy.

✅ For faster delivery, use <b>TRX</b>, <b>ETH</b> or <b>USDT-TRC20</b>.
"""
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(
        user_id,
        warning_msg,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
