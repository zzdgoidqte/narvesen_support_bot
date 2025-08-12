# middlewares/database.py
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject
from controllers.db_controller import DatabaseController  # Updated import path

class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware to pass the DatabaseController to handlers.
    """
    def __init__(self, db: DatabaseController):
        self.db = db

    async def __call__(self, handler, event: TelegramObject, data: dict):
        data["db"] = self.db
        return await handler(event, data)