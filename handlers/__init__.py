from aiogram import Dispatcher

from .automated_replies import misc_replies
from . import (
    start_handler,
    misc_handler
)


def register_handlers(dp: Dispatcher):
    """
    Register all routers with the provided Dispatcher.
    """
    dp.include_routers(
        start_handler.router,
        misc_handler.router
    )
