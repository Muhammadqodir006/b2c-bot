import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers.client import onboarding, main_menu, profile


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.client_bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(onboarding.router)
    dp.include_router(main_menu.router)
    dp.include_router(profile.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())