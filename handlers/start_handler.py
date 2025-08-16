from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatType
from utils.logger import logger
from controllers.db_controller import DatabaseController
from utils.helpers import escape_markdown_v1, is_similar_to_start

router = Router()
@router.message(lambda message: message.chat.type == ChatType.PRIVATE and is_similar_to_start(message.text))
async def start_handler(
    message: Message, state: FSMContext, db: DatabaseController
):
    """Handle /start command by checking user orders and sending appropriate welcome message in English, Latvian, Estonian, and Russian."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        user_has_orders = await db.get_order_count_for_user(user_id)
        bot_settings = await db.get_bot_settings()
        bot_username = bot_settings.get('bot_username', '')

        if not user_has_orders:
            rejection_text = (
                "🇬🇧 <b>Access Denied</b>\n"
                f"You must have an active order with @{bot_username} to use this support bot.\n"
                "Please place an order first and then try again!\n\n"
                
                "🇱🇻 <b>Piekļuve liegta</b>\n"
                f"Jums jābūt aktīvam pasūtījumam ar @{bot_username}, lai izmantotu šo atbalsta botu.\n"
                "Lūdzu, vispirms veiciet pasūtījumu un mēģiniet vēlreiz!\n\n"
                
                "🇪🇪 <b>Ligipääs keelatud</b>\n"
                f"Sul peab olema aktiivne tellimus @{bot_username} kaudu, et seda tugibotti kasutada.\n"
                "Palun tee kõigepealt tellimus ja proovi siis uuesti!\n\n"
                
                "🇷🇺 <b>Доступ запрещён</b>\n"
                f"У вас должен быть активный заказ в @{bot_username}, чтобы использовать этот бот поддержки.\n"
                "Пожалуйста, сначала сделайте заказ и попробуйте снова!"
            )
            await message.answer(
                text=rejection_text,
                parse_mode="HTML"
            )
            logger.info(f"User {user_id} (@{username}) denied access - no orders found")
            return

        # Welcome message for users with orders
        welcome_text = (
            "🇬🇧 <b>Welcome to Narvesen Support!</b>\n"
            f"Please describe your issue with @{bot_username}. You can attach a photo or video if needed.\n\n"
            
            "🇱🇻 <b>Sveiki, Narvesen atbalsts!</b>\n"
            f"Lūdzu, aprakstiet savu problēmu ar @{bot_username}. Varat pievienot foto vai video.\n\n"
            
            "🇪🇪 <b>Tere tulemast Narveseni tugiteenusesse!</b>\n"
            f"Palun kirjelda oma probleemi @{bot_username} kasutamisel. Vajadusel lisa foto või video.\n\n"
            
            "🇷🇺 <b>Добро пожаловать в поддержку Narvesen!</b>\n"
            f"Опишите вашу проблему с @{bot_username}. При необходимости прикрепите фото или видео.\n\n"
        )

        # Send welcome message
        await message.answer_photo(
            photo=FSInputFile("data/narvesen.jpg"),
            caption=welcome_text,
            parse_mode="HTML"
        )

        # Log the interaction
        logger.info(f"User {user_id} (@{username}) started the bot with active orders")

        # Clear any existing state
        await state.clear()

    except Exception as e:
        logger.error(f"Error in handle_start: {str(e)}")
        error_text = (
            "🇬🇧 <b>Oops!</b> Something went wrong. Please try again later.\n\n"
            "🇱🇻 <b>Ak vai!</b> Kaut kas nogāja greizi. Lūdzu, mēģiniet vēlreiz vēlāk.\n\n"
            "🇪🇪 <b>Oih!</b> Midagi läks valesti. Palun proovi hiljem uuesti.\n\n"
            "🇷🇺 <b>Ой!</b> Что-то пошло не так. Пожалуйста, попробуйте снова позже."
        )
        await message.answer(
            text=error_text,
            parse_mode="HTML"
        )
