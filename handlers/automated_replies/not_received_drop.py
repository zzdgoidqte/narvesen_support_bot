import asyncio
import random

async def handle_not_received_drop(db, bot, user, ticket, lang):
    user_id = user.get("user_id")

    # Multiple message variations for each language
    message_variations = {
        "lv": [
            [
                "Pamēģini parakt dziļāk, reizēm tas ir 10-15 cm zem zemes",
                "Vai esi pārliecināts, ka tā ir īstā vieta?",
                "Ja tiešām vēl joprojām neatrodi, tad atsūti pāris bildes vai īsu video ar tuvplānu dropa vietai un apkārtnei"
            ],
            [
                "Iespējams jārok dziļāk, mēdz būt pat 10-15 cm zemē",
                "Pārbaudi, vai esi pareizajā vietā",
                "Ja tiešām vēl joprojām neatrodi, tad atsūti video vai dažas bildes ar vietas un apkārtnes tuvplānu"
            ],
            [
                "Paroc dziļāk - bieži vien ir zemē līdz 15 cm",
                "Vai tiešām esi īstajā lokācijā?",
                "Ja tiešām vēl joprojām neatrodi, tad atsūti bildes vai video ar detalizētu skatu uz dropu un tā apkārtni"
            ],
            [
                "Reizēm tas ir aprakts dziļāk - pārbaudi līdz 15 cm",
                "Vai vieta sakrīt ar koordinātēm?",
                "Ja tiešām vēl joprojām neatrodi, tad iemet pāris bildes vai video ar dropa vietas tuvplānu un apkārtni"
            ]
        ],
        "ee": [
            [
                "Proovi sügavamalt kaevata, see võib olla 10-15 cm sügavusel",
                "Kas oled kindel, et see on õige koht?",
                "Kui sa tõesti ikka veel ei leia, saada mõned pildid või lühike video koos lähivõttega drop’i kohast ja ümbrusest"
            ],
            [
                "Vahel tuleb veidi sügavamale kaevata - kuni 15 cm",
                "Oled sa õiges kohas?",
                "Kui ikka veel ei leia, saada video või fotod, kus on näha ka drop’i koht ja selle ümbrus lähivõttes"
            ],
            [
                "Vaata, kas see pole sügavamal - 10-15 cm allpool",
                "Kas koordinaadid klapivad?",
                "Kui tõesti ikka veel ei leia, saada tõendiks pildid või video, kus on selgelt näha asukoht ja taust"
            ],
            [
                "Kaevu natuke sügavamale, vahel on see päris sügaval",
                "Oled sa kindel, et kontrollisid õiget kohta?",
                "Kui ikka veel ei leia, pane mõned pildid või video, kus on lähivaade drop’i kohale ja ümbrusele"
            ]
        ],
        "ru": [
            [
                "Попробуй копнуть глубже, иногда оно на 10-15 см в земле",
                "Ты уверен, что это то самое место?",
                "Если всё ещё не можешь найти, пришли фото или видео с крупным планом места закладки и окружения"
            ],
            [
                "Иногда нужно копнуть - может быть на глубине до 15 см",
                "Проверь координаты, точно там ищешь?",
                "Если всё ещё не находишь, скинь видео или фото, где видно точку и её окружение крупным планом"
            ],
            [
                "Бывает зарыто глубже, до 10-15 см",
                "Убедись, что это правильная точка",
                "Если всё ещё не нашёл, пришли фото или видео, где чётко видно место и фон"
            ],
            [
                "Может быть глубже закопано - проверь получше",
                "Ты точно в нужном месте смотришь?",
                "Если всё ещё не нашёл, кинь пару фоток или видео с крупным планом закладки и того, что рядом"
            ]
        ],
        "eng": [
            [
                "Try digging deeper, it might be 10-15cm underground",
                "Are you sure you're at the right spot?",
                "If you're still not finding it, send a few pics or a short video including a close-up of the drop spot and surroundings"
            ],
            [
                "Sometimes it's buried deeper - check 10-15cm down",
                "Double-check if you're in the correct location",
                "If you're still having trouble, send a video or photos clearly showing the spot and nearby area"
            ],
            [
                "It might be deeper, try checking below the surface",
                "Could you be off from the actual spot?",
                "If you still can't find it, send photos or a video with a clear close-up of the drop location and its surroundings"
            ],
            [
                "Dig a little deeper - sometimes it's 10-15cm in",
                "Sure you're at the right coordinates?",
                "If you're really still not finding it, drop a couple pics or a video that shows the drop point and the surrounding area clearly"
            ]
        ]
    }


    # Use English as fallback
    selected_variation = random.choice(message_variations.get(lang, message_variations["eng"]))

    await bot.send_message(user_id, selected_variation[0])
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, selected_variation[1])
