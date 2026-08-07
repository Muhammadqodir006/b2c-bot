import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from handlers.master import onboarding, profile, schedule

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.master_bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(onboarding.router)
    dp.include_router(profile.router)
    dp.include_router(schedule.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())