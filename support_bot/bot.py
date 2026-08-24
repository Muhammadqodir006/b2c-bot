import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Salom! Savol yoki muammoingiz bo'lsa, shu yerga yozing — "
        "administratorga yetkazamiz."
    )


@router.message(F.text)
async def forward_to_admin(message: Message, bot: Bot):
    user_info = (
        f"📩 Yangi murojaat\n"
        f"👤 {message.from_user.full_name} "
        f"(@{message.from_user.username or '—'}, ID: {message.from_user.id})"
    )

    for admin_id in settings.admin_id_list:
        await bot.send_message(admin_id, user_info)
        await bot.forward_message(
            chat_id=admin_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )

    await message.answer("✅ Xabaringiz administratorga yuborildi.")


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.support_bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())