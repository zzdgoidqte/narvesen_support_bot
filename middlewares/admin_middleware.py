from aiogram import BaseMiddleware, Bot
from aiogram.types import Update, Chat, Message
from aiogram.enums import ChatType
from typing import Callable, Awaitable, Any, Dict
from controllers.db_controller import DatabaseController
from utils.logger import logger


class AdminMiddleware(BaseMiddleware):
    def __init__(self, db: DatabaseController, bot: Bot):
        self.db = db
        self.bot = bot
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        try:
            msg = event.message
            if not msg or msg.chat.type != ChatType.GROUP:
                return await handler(event, data)

            user = msg.from_user
            if not user:
                return await handler(event, data)

            is_admin = await self.db.is_role(user.id, 'admin')
            if is_admin:
                # Fetch chat info from Bot API
                chat: Chat = await self.bot.get_chat(msg.chat.id)
                user_id = chat.description  # Assuming description is user_id
                user_active_tickets = await self.db.get_support_tickets(exclude_closed=True, user_id=int(user_id))
                if not user_active_tickets:
                    await self.bot.send_message(msg.chat.id, "‼️MESSAGE NOT SENT‼️\n\nℹ️ You can't chat with the client until this bot sends another ticket from him!\nℹ️ Write him a private message from your account if you need to talk to him.")
                    return await handler(event, data)

                # Send the message content to the user
                logger.info(f"Admin message in group with {user_id}: {self.get_message_content(msg)}")
                await self.send_content(user_id, msg)

            return await handler(event, data)

        except Exception as e:
            logger.error(f"Error in admin middleware: {e}")
            return await handler(event, data)

    def get_message_content(self, message: Message) -> str:
        """Determine the content to log and save based on message type."""
        if message.text:
            return message.text
        elif message.photo:
            return "(photo)"
        elif message.video:
            return "(video)"
        elif message.document:
            return "(document)"
        elif message.sticker:
            return "(sticker)"
        elif message.audio:
            return "(audio)"
        elif message.voice:
            return "(voice)"
        elif message.animation:
            return "(animation)"
        elif message.video_note:
            return "(video_note)"
        else:
            return "(other)"

    async def send_content(self, user_id: int | str, message: Message):
        """Send the intercepted content to a user."""
        if message.text:
            await self.bot.send_message(user_id, message.text)

        elif message.photo:
            largest_photo = message.photo[-1]
            await self.bot.send_photo(user_id, largest_photo.file_id, caption=message.caption)

        elif message.video:
            await self.bot.send_video(user_id, message.video.file_id, caption=message.caption)

        elif message.document:
            await self.bot.send_document(user_id, message.document.file_id, caption=message.caption)

        elif message.sticker:
            await self.bot.send_sticker(user_id, message.sticker.file_id)

        elif message.audio:
            await self.bot.send_audio(user_id, message.audio.file_id, caption=message.caption)

        elif message.voice:
            await self.bot.send_voice(user_id, message.voice.file_id, caption=message.caption)

        elif message.animation:
            await self.bot.send_animation(user_id, message.animation.file_id, caption=message.caption)

        elif message.video_note:
            await self.bot.send_video_note(user_id, message.video_note.file_id)

        else:
            logger.error(f"Unsupported content type when sending message to user from group: {message}")
