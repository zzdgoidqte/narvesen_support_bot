import asyncio
import random
from utils.helpers import query_nano_gpt

async def handle_not_received_drop(db, bot, user, ticket, lang):
    user_id = user.get("user_id")

    target_lang = lang if lang in ["lv", "ee", "ru", "eng"] else "eng"

    message1_lv = "Pamēģini parakt dziļāk, reizēm drops ir 10-15 cm zem zemes"
    message2_lv = "Vai esi pārliecināts, ka tā ir īstā vieta?"
    message3_lv = "Ja tiešām vēl joprojām neatrodi, tad atsūti pāris bildes vai īsu video ar tuvplānu dropa vietai un apkārtnei"

    prompt = f"""
You are a translation and localization assistant.

Translate and paraphrase the following 3 Latvian messages into {target_lang}.

Return exactly 3 lines separated only by line breaks (\\n):
- Line 1: paraphrase of the first message
- Line 2: paraphrase of the second message
- Line 3: paraphrase of the third message

Important:
- Each line must NOT include any numbering, bullet points, or extra characters/spacings before the text
- The first line must include that the drop is 10-15cm underground
- Use natural grammar and vocabulary for the target language

Message 1:
\"\"\"{message1_lv}\"\"\"

Message 2:
\"\"\"{message2_lv}\"\"\"

Message 3:
\"\"\"{message3_lv}\"\"\"
"""

    ai_response = await query_nano_gpt(prompt, max_tokens=250)

    fallback_variations = {
        "lv": [
            "Paroc dziļāk – bieži drops ir līdz 10–15 cm zemē",
            "Vai tiešām esi īstajā vietā?",
            "Ja vēl neatrodi, atsūti dažas bildes vai video ar tuvplānu dropa vietai un apkārtnei"
        ],
        "ee": [
            "Kaevu natuke sügavamale – drop võib olla 10–15 cm sügavusel",
            "Oled kindel, et oled õiges kohas?",
            "Kui ikka veel ei leia, saada mõned pildid või video, kus on näha drop’i koht ja ümbrus lähivaates"
        ],
        "ru": [
            "Попробуй копнуть глубже – дроп может быть на глубине 10–15 см",
            "Ты уверен, что смотришь в правильном месте?",
            "Если всё ещё не нашёл, пришли фото или видео с крупным планом дропа и её окружения"
        ],
        "eng": [
            "Try digging deeper – the drop might be 10–15cm underground",
            "Are you sure you're at the right spot?",
            "If you still can't find it, send a few photos or a video clearly showing the drop location and surroundings"
        ]
    }

    def is_valid_line(line):
        return line and 5 < len(line) < 300

    def distinct_enough(lines):
        # Simple check: all lines must be distinct
        return len(set(lines)) == len(lines)

    if ai_response:
        ai_response = ai_response.replace("\\n", "\n")
        lines = [line.strip() for line in ai_response.strip().split("\n") if is_valid_line(line)]
        if len(lines) == 3 and distinct_enough(lines):
            msg1, msg2, msg3 = lines
        else:
            msg1, msg2, msg3 = fallback_variations.get(target_lang, fallback_variations["eng"])
    else:
        msg1, msg2, msg3 = fallback_variations.get(target_lang, fallback_variations["eng"])

    await bot.send_message(user_id, msg1)
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, msg2)
    await asyncio.sleep(random.uniform(4, 6))
    await bot.send_message(user_id, msg3)
