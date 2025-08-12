from aiogram import BaseMiddleware, Bot
from aiogram.types import Update, Message
from aiogram.enums import ChatType
from typing import Callable, Awaitable, Any, Dict
from controllers.db_controller import DatabaseController
from utils.logger import logger
from utils.helpers import is_similar_to_start


class UserMiddleware(BaseMiddleware):
    def __init__(self, db: DatabaseController, bot: Bot):
        self.db = db
        self.bot = bot # Aiogram bot
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        try:
            msg = event.message or event.edited_message
            if not msg:
                return await handler(event, data)

            user = msg.from_user
            if await self.db.is_muted(int(user.id)):
                return await handler(event, data)

            # Handle group/channel messages
            if msg.chat.type != ChatType.PRIVATE:
                return await handler(event, data)
            
            # Handle edited messages
            if event.edited_message:
                message = await self.db.get_message(msg.chat.id, msg.message_id)
                new_text = msg.text
                if not message.get('messages_forwarded'):
                    # Register the edit only if it hasnt been replied to
                    await self.db.update_edited_message(msg.chat.id, msg.message_id, new_text)
                else:
                    # If messages have been forwarded to admin then send the update to admin
                    user_group_id = await self.db.get_user_group_id(msg.chat.id)
                    await self.bot.send_message(chat_id=user_group_id, text=f"(EDITED MESSAGE)\n{new_text}")
                return await handler(event, data)


            # Handle command messages (e.g., /start, /help)
            if msg.text and msg.text.startswith("/"):
                return await handler(event, data)

            # Handle messages similar to the start command
            if msg.text and is_similar_to_start(msg.text):
                return await handler(event, data)
            
            # Create a ticket and save to db for later processing in bot_response.py
            content = self.get_message_content(msg)
            users_has_forwarded_and_unclosed_ticket = await self.db.get_support_tickets(exclude_closed=True, exclude_messages_unforwarded=True, user_id=user.id)

            if users_has_forwarded_and_unclosed_ticket: # Make admin respond
                user_group_id = await self.db.get_user_group_id(user.id)
                await self.bot.forward_message(
                    user_group_id,
                    user.id,
                    msg.message_id
                )
                await self.db.save_user_message(
                    user_id=user.id,
                    message_id=msg.message_id,
                    user_text=content,
                    replied=True
                )
            else: # Make AI respond
                await self.db.save_user_message(
                    user_id=user.id,
                    message_id=msg.message_id,
                    user_text=content
                )

            logger.info(f"{user.first_name} ({user.id}): {content}")
            return await handler(event, data)

        except Exception as e:
            logger.error(
                f"Error in messages middleware for user {event.message.from_user.id if event.message else 'unknown'}: {e}"
            )
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
        
