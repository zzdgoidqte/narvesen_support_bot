import asyncio
import random

async def handle_not_received_drop(db, bot, user, ticket, lang):
    user_id = user.get("user_id")

    # Multiple message variations for each language
    message_variations = {
        "lv": [
            ["Atsūti pāris bildes vai īsu video kā pierādījumu", "Iekļauj tuvplānu ar dropa vietu un apkārtni"],
            ["Atsūti pierādījumam video vai pāris bildes", "Uztver arī tuvplānu dropa lokācijai un videi"],
            ["Atsūti pierādījumam bildes vai video", "Tuvplāns ar dropu un apkārtni arī vajadzīgs"],
            ["Iemet pāris bildes vai video kā pierādījumu", "Uztaisi tuvplānu ar vietu kur nometi un apkārtni"]
        ],
        "ee": [
            ["Saada mõned pildid või lühike video tõendina", "Lisa ka lähivõte drop’i kohast ja ümbrusest"],
            ["Saada video või mõned pildid tõendiks", "Võta ka lähivõte drop’i kohast ja taustast"],
            ["Saada tõendiks pildid või video", "Vaja ka lähivõtet drop’i asukohast ja ümbrusest"],
            ["Pane mõned pildid või video tõendiks", "Tee lähivõte drop’i kohast ja selle ümbrusest"]
        ],
        "ru": [
            ["Пришли пару фото или короткое видео как доказательство", "Добавь крупный план места закладки и окружения"],
            ["Скинь видео или фото как подтверждение", "Сделай крупный план места и фона"],
            ["Пришли фото или видео как подтверждение", "Нужен крупный план места и окружения"],
            ["Кинь пару фоток или видео в подтверждение", "Сделай крупный план точки и того что вокруг"]
        ],
        "eng": [
            ["Send a few pics or a short video as proof", "Include a close-up of the drop spot and surroundings"],
            ["Send a video or some photos for proof", "Include a close-up of the spot and background"],
            ["Send photos or a video for proof", "Need a close-up of the drop and the area"],
            ["Drop a couple pics or a video for proof", "Get a close-up of the spot and what’s around"]
        ]
    }

    # Use English as fallback
    selected_variation = random.choice(message_variations.get(lang, message_variations["eng"]))

    await bot.send_message(user_id, selected_variation[0])
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, selected_variation[1])
