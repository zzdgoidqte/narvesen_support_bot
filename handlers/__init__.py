from aiogram import Dispatcher

from . import (
    start_handler,
    misc_handler,
    close_ticket_handler
)


def register_handlers(dp: Dispatcher):
    """
    Register all routers with the provided Dispatcher.
    """
    dp.include_routers(
        start_handler.router,
        misc_handler.router,
        close_ticket_handler.router
    )
