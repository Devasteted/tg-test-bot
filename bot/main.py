import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import load_config
from bot.db import Database
from bot.handlers import admin, user


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = load_config()
    db = Database(config.db_path)
    await db.init()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Зависимости, доступные в хендлерах по имени аргумента
    dp["config"] = config
    dp["db"] = db

    # Админ-роутер работает только для пользователей из ADMIN_IDS
    admin.router.message.filter(lambda m: admin.is_admin(m, config))

    dp.include_router(admin.router)
    dp.include_router(user.router)

    logging.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
