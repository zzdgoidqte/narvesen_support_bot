from controllers.db_controller import DatabaseController
import asyncio
import random
from telethon.tl.functions.messages import SendMultiMediaRequest
from telethon.tl.types import (
    InputMediaUploadedPhoto,
    InputSingleMedia,
)



async def handle_payment_help(db, client, user, ticket, lang):
    await db.close_support_ticket(ticket.get('ticket_id'))
    user_id = user.get("user_id")

    # --- Localized crypto guide messages ---
    crypto_guides = {
    "lv": """
<b>💸 Kā maksāt ar kriptovalūtu (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Iegādājies kriptovalūtu jebkurā makā - iesakām <a href="https://www.bybit.com/">Bybit</a>.

2. Nosūti precīzu summu vai vairāk uz adresi, ko mēs tev sniegsim pasūtījuma veikšanas laikā.

<b>⚠️ Ņem vērā:</b> BTC darījumi aizņem būtiski ilgāku laiku nekā citas kriptovalūtas, kas var aizkavēt pasūtījuma apstrādi.

3. Kad maksājums būs apstiprināts, bots nosūtīs tev dropu.
""",
    "ee": """
<b>💸 Kuidas maksta krüptoga (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Osta krüpto ükskõik millise rahakoti kaudu - soovitame <a href="https://www.bybit.com/">Bybit</a>.

2. Saada täpne summa või rohkem aadressile, mille anname tellimuse esitamisel.

<b>⚠️ Pane tähele:</b> BTC tehingud võtavad märgatavalt kauem aega kui muud krüptod ja võivad põhjustada viivitusi tellimuse kinnitamisel.

3. Kui makse on kinnitatud, saadab bot sulle dropi.
""",
    "ru": """
<b>💸 Как оплатить криптовалютой (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Купите криптовалюту в любом кошельке - мы рекомендуем <a href="https://www.bybit.com/">Bybit</a>.

2. Отправьте точную сумму или больше на адрес, который мы вам дадим при оформлении заказа.

<b>⚠️ Обратите внимание:</b> Транзакции в BTC обрабатываются значительно дольше, чем в других валютах, что может задержать ваш заказ.

3. После подтверждения оплаты бот отправит вам дроп.
""",
    "eng": """
<b>💸 How to Pay with Crypto (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Buy crypto using any wallet - we recommend <a href="https://www.bybit.com/">Bybit</a>.

2. Send the exact amount or more to the wallet address we give you when you make an order.

<b>⚠️ Note:</b> BTC transactions take significantly longer to process than other cryptocurrencies and may delay your order.

3. Once the payment is confirmed, the bot will send you the drop.
"""
}



    # --- Localized card payment instructions ---
    card_payment_captions = {
    "lv": """
<b>💳 Kā maksāt ar karti</b>

1. Nokopē adresi, kuru tev nosūtīs bots.

2. Ej uz <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Izvēlies LTC, ievadi "Payment amount" summu "You get" laukā, spied "Buy". Pēc tam ievieto adresi, kuru nosūtīja bots un ievadi kartes datus.

✅ Kad maksājums būs apstiprināts, bots nosūtīs tev dropu.

<b>🔒 Piezīme:</b> Mercuryo nav mūsu īpašumā - tava informācija paliek privāta. Ja gadījumā rodas problēmas saistībā ar Mercuryo, kontaktējies ar viņu atbalsta komandu, nevis mums. Mēs neesam atbildīgi par Mercuryo samaksas problēmām un kavējumiem!

⚠️ Apmaiņas maksa tiek piemērota. Kriptomaksājumi ir lētāki un ātrāki!
""",
    "ee": """
<b>💳 Kuidas maksta kaardiga</b>

1. Kopeeri aadress, mille saadab sulle bot.

2. Mine lehele <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Vali LTC, sisesta "Payment amount" summa lahtrisse "You get", vajuta "Buy". Seejärel kleebi aadress, mille saatis bot, ja sisesta kaardiandmed.

✅ Kui makse on kinnitatud, saadab bot sulle tellimuse.

<b>🔒 Märkus:</b> Mercuryo ei kuulu meile - sinu info jääb konfidentsiaalseks. Kui tekib probleeme Mercuryoga, võta ühendust nende klienditoega, mitte meiega. Me ei vastuta makseviivituste või probleemide eest Mercuryo platvormil!

⚠️ Vahetustasu võib lisanduda. Krüptoga on odavam ja kiirem!
""",
    "ru": """
<b>💳 Как оплатить картой</b>

1. Скопируйте адрес, который отправит вам бот.

2. Перейдите на сайт <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Выберите LTC, введите сумму из "Payment amount" в поле "You get", нажмите "Buy". Затем вставьте адрес, который отправил бот, и введите данные карты.

✅ Когда оплата будет подтверждена, бот отправит вам дроп.

<b>🔒 Примечание:</b> Mercuryo не принадлежит нам - ваша информация остаётся конфиденциальной. Если возникнут проблемы с Mercuryo, обращайтесь в их службу поддержки, а не к нам. Мы не несём ответственности за задержки и проблемы с оплатой на стороне Mercuryo!

⚠️ Взимается комиссия обмена. Оплата криптовалютой дешевле и быстрее!
""",
    "eng": """
<b>💳 How to Pay with Card</b>

1. Copy the wallet address sent to you by the bot.

2. Go to <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Select LTC, enter the "Payment amount" number into the "You get" field, click "Buy". Then paste the address sent by the bot and enter your card details.

✅ Once the payment is confirmed, the bot will send you the drop.

<b>🔒 Note:</b> Mercuryo is not owned by us - your information remains private. If you have issues with Mercuryo, contact their support team, not us. We're not responsible for delays or payment problems on their side!

⚠️ Exchange fees apply. Crypto payments are cheaper and faster!
"""
}
    entity = await client.get_input_entity(user_id)

    # --- Get texts by language ---
    crypto_text = crypto_guides.get(lang, crypto_guides["eng"])
    card_caption = card_payment_captions.get(lang, card_payment_captions["eng"])

    # --- Send crypto guide ---
    await client.send_message(
        user_id,
        crypto_text,
        parse_mode="HTML",
        disable_web_page_preview=True
        )
    photo1 = await client.upload_file("data/card_payment_1.jpg")
    photo2 = await client.upload_file("data/card_payment_2.jpg")

    # Build media group
    media_group = [
        InputSingleMedia(
            media=InputMediaUploadedPhoto(file=photo1),
            message=card_caption,
            entities=[]
        ),
        InputSingleMedia(
            media=InputMediaUploadedPhoto(file=photo2),
            message="",  # only first item should have a caption
        ),
    ]

    # Send media group
    await client(SendMultiMediaRequest(
        peer=entity,
        multi_media=media_group
    ))