from aiogram import Bot
from aiogram.types import InputMediaPhoto, FSInputFile
from controllers.db_controller import DatabaseController
from handlers.bot_workflow.forward_ticket_to_admin import forward_ticket_to_admin
import asyncio
import random


async def handle_payment_help(db, bot, user, ticket, lang):
    await db.close_support_ticket(ticket.get('ticket_id'))
    user_id = user.get("user_id")

    # --- Localized crypto guide messages ---
    crypto_guides = {
    "lv": """
<b>💸 Kā maksāt ar kriptovalūtu (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Iegādājies kriptovalūtu jebkurā makā – iesakām <a href="https://www.bybit.com/">Bybit</a>.

2. Nosūti precīzu summu uz maku, ko mēs tev sniegsim pasūtījuma veikšanas laikā.

<b>⚠️ Ņem vērā:</b> BTC darījumi aizņem būtiski ilgāku laiku nekā citas kriptovalūtas, kas var aizkavēt pasūtījuma apstrādi.

3. Kad maksājums būs apstiprināts, tu saņemsi savu pasūtījumu.
""",
    "ee": """
<b>💸 Kuidas maksta krüptoga (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Osta krüpto ükskõik millise rahakoti kaudu – soovitame <a href="https://www.bybit.com/">Bybit</a>.

2. Saada täpne summa aadressile, mille anname tellimuse esitamisel.

<b>⚠️ Pane tähele:</b> BTC tehingud võtavad märgatavalt kauem aega kui muud krüptod ja võivad põhjustada viivitusi tellimuse kinnitamisel.

3. Kui makse on kinnitatud, saad oma tellimuse.
""",
    "ru": """
<b>💸 Как оплатить криптовалютой (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Купите криптовалюту в любом кошельке — мы рекомендуем <a href="https://www.bybit.com/">Bybit</a>.

2. Отправьте точную сумму на адрес, который мы вам дадим при оформлении заказа.

<b>⚠️ Обратите внимание:</b> Транзакции в BTC обрабатываются значительно дольше, чем в других валютах, что может задержать ваш заказ.

3. После подтверждения оплаты вы получите свой заказ.
""",
    "eng": """
<b>💸 How to Pay with Crypto (BTC, ETH, LTC, TRX, USDT-TRC20)</b>

1. Buy crypto using any wallet – we recommend <a href="https://www.bybit.com/">Bybit</a>.

2. Send the exact amount to the wallet address we give you when you make an order.

<b>⚠️ Note:</b> BTC transactions take significantly longer to process than other cryptocurrencies and may delay your order.

3. Once confirmed, you’ll get your order.
"""
    }


    # --- Localized card payment instructions ---
    card_payment_captions = {
        "lv": """
<b>💳 Kā maksāt ar karti</b>

1. Nokopē adresi, kuru mēs nosūtīsim.

2. Ej uz <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Izvēlies LTC, ievadi summu "You get" laukā, spied "Buy". Pēc tam ielīmē mūsu adresi un ievadi kartes datus.

✅ Kad mēs saņemam maksājumu, pasūtījums tiek izsūtīts.

<b>🔒 Piezīme:</b> Mercuryo nav mūsu īpašumā - tava informācija paliek privāta.

⚠️ Apmaiņas maksa tiek piemērota. Kriptomaksājumi ir lētāki un ātrāki!
""",
        "ee": """
<b>💳 Kuidas maksta kaardiga</b>

1. Kopeeri aadress, mille me saadame.

2. Mine lehele <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Vali LTC, sisesta summa lahtrisse "You get", vajuta "Buy". Seejärel kleebi aadress ja sisesta kaardiandmed.

✅ Kui me saame makse kätte, saadetakse sinu tellimus.

<b>🔒 Märkus:</b> Mercuryo ei kuulu meile - sinu andmed jäävad konfidentsiaalseks.

⚠️ Võib lisanduda vahetustasu. Krüptoga on odavam ja kiirem!
""",
        "ru": """
<b>💳 Как оплатить картой</b>

1. Скопируйте адрес, который мы отправим.

2. Перейдите на <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Выберите LTC, введите сумму в поле "You get", нажмите "Buy". Затем вставьте наш адрес и введите данные карты.

✅ После получения оплаты мы отправим ваш заказ.

<b>🔒 Примечание:</b> Mercuryo нам не принадлежит - ваша информация остается конфиденциальной.

⚠️ Комиссии биржи применимы. Криптовалюта дешевле и быстрее!
""",
        "eng": """
<b>💳 How to Pay with Card</b>

1. Copy the wallet address we send.

2. Go to <a href="https://exchange.mercuryo.io/">exchange.mercuryo.io</a>.

3. Pick LTC, paste the LTC amount under "You get", click buy. Then paste in the wallet address. Then enter your card details and pay.

✅ Once we get the crypto, your order is sent.

<b>🔒 Note:</b> We don’t own Mercuryo - your info stays private.

⚠️ Exchange fees apply. Crypto payments are cheaper & faster!
"""
    }

    # --- Get texts by language ---
    crypto_text = crypto_guides.get(lang, crypto_guides["eng"])
    card_caption = card_payment_captions.get(lang, card_payment_captions["eng"])

    # --- Send crypto guide ---
    await bot.send_message(
        user_id,
        crypto_text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    # --- Send card payment media ---
    photo1 = FSInputFile("data/card_payment_1.jpg")
    photo2 = FSInputFile("data/card_payment_2.jpg")
    media = [
        InputMediaPhoto(media=photo1, caption=card_caption, parse_mode="HTML"),
        InputMediaPhoto(media=photo2)
    ]
    await bot.send_media_group(user_id, media)
