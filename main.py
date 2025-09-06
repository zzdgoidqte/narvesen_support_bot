import asyncio

from aiogram import Bot, Dispatcher
from handlers import register_handlers
from handlers.bot_workflow import *
from config.config import Config
from controllers.db_controller import DatabaseController
from middlewares import DatabaseMiddleware, UserMiddleware, AdminMiddleware
from utils.logger import logger


async def main():
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher()

    # Initialize database
    db = await DatabaseController(bot).initialize()

    # Register middlewares
    dp.update.middleware(UserMiddleware(db, bot))
    dp.update.middleware(AdminMiddleware(db, bot))
    dp.message.middleware(DatabaseMiddleware(db))
    dp.callback_query.middleware(DatabaseMiddleware(db)) 

    # Register handlers
    register_handlers(dp)

    # Register async tasks
    asyncio.create_task(handle_unforwarded_tickets(db, bot))
    asyncio.create_task(delete_unused_groups(db))

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot polling failed: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot session closed")
        await db.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
