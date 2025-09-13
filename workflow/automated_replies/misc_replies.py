import asyncio
import random

async def handle_voice_message(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await bot.send_message(user_id, "Can you please send text instead of a voice message?")
    await asyncio.sleep(random.uniform(6, 8))
    await bot.send_message(user_id, "My phones audio doesn't work")

async def handle_thanks(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await db.close_support_ticket(ticket.get('ticket_id'))
    await bot.send_message(user_id, "👍")
    return

def get_time_based_message(lang: str, hour: int) -> str:
    is_late = 22 <= hour <= 23
    is_early = 0 <= hour < 7

    if lang == "lv":
        return (
            "Ņemot vērā, ka ir ļoti vēls, šobrīd nevaram garantēt tūlītēju risinājumu." if is_late else
            "Ņemot vērā, ka ir ļoti agrs rīts, šobrīd nevaram garantēt tūlītēju risinājumu."
        )
    elif lang == "ee":
        return (
            "Kuna on väga hiline aeg, ei saa me praegu lahendust garanteerida." if is_late else
            "Kuna on väga varajane hommik, ei saa me praegu lahendust garanteerida."
        )
    elif lang == "ru":
        return (
            "Сейчас очень поздно, поэтому мы не можем гарантировать быстрое решение." if is_late else
            "Сейчас очень рано утром, поэтому мы не можем гарантировать быстрое решение."
        )
    else:  # eng or fallback
        return (
            "Since it is very late, we can't guarantee to resolve the issue right now." if is_late else
            "Since it is very early in the morning, we can't guarantee to resolve the issue right now."
        )