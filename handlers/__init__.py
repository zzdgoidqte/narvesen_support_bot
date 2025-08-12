from aiogram import Dispatcher

from .replies import payment_help
from . import (
    start_handler
)


def register_handlers(dp: Dispatcher):
    """
    Register all routers with the provided Dispatcher.
    """
    dp.include_routers(
        start_handler.router,
        payment_help.router
    )
