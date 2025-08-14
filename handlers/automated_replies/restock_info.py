async def handle_restock_info(db, bot, user, ticket, lang):
    user_id = user.get("user_id")
    await db.close_support_ticket(ticket.get('ticket_id'))

    messages = {
        "lv": "Pašlaik mums nav informācijas par šo preci, bet mēs cenšamies pēc iespējas ātrāk atjaunot krājumus visiem produktiem.",
        "ee": "Hetkel pole meil selle toote kohta infot, kuid püüame kõik tooted võimalikult kiiresti laost uuesti kättesaadavaks teha.",
        "ru": "Сейчас у нас нет информации об этом товаре, но мы стараемся как можно быстрее пополнить все запасы.",
        "eng": "Currently we don’t have any info about that, but we’re trying to restock every product as soon as possible."
    }

    message_text = messages.get(lang, messages["eng"])

    await bot.send_message(user_id, message_text)
