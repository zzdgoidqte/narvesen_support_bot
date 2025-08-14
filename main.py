import asyncio

from aiogram import Bot, Dispatcher
from handlers import register_handlers
from handle_user_input import handle_user_input
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
    asyncio.create_task(handle_user_input(db, bot))

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
