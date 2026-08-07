from aiogram import Router, F
from aiogram.types import Message
from database.repositories.user_repo import get_user

router = Router()

@router.message(F.text.in_(["📍 Yaqin atrofdagi salonlar", "📍 Салоны рядом"]))
async def nearby_salons(message: Message):
    user = await get_user(message.from_user.id)
    lang = user.language if user else "uz"
    text = (
        "Bu bo'lim tez orada tayyor bo'ladi 🔧"
        if lang == "uz"
        else "Этот раздел скоро будет готов 🔧"
    )
    await message.answer(text)

@router.message(F.text.in_(["🔍 Kategoriyalar", "🔍 Категории"]))
async def categories(message: Message):
    user = await get_user(message.from_user.id)
    lang = user.language if user else "uz"
    text = (
        "Bu bo'lim tez orada tayyor bo'ladi 🔧"
        if lang == "uz"
        else "Этот раздел скоро будет готов 🔧"
    )
    await message.answer(text)