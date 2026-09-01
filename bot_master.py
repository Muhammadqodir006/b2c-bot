import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from config import settings
from handlers.master import onboarding, profile, schedule, notifications, admin, salon_registration


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.master_bot_token)
    storage = RedisStorage.from_url(
        settings.redis_url,
        key_builder=DefaultKeyBuilder(with_bot_id=True, prefix="fsm_master")
    )
    dp = Dispatcher(storage=storage)

    dp.include_router(admin.router)
    dp.include_router(onboarding.router)
    dp.include_router(profile.router)
    dp.include_router(schedule.router)
    dp.include_router(notifications.router)
    dp.include_router(salon_registration.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
