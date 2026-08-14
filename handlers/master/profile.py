from aiogram import Router, F
from aiogram.types import Message
from database.repositories.salon_repo import (
    get_master_by_telegram_id,
    update_master_language,
)
from handlers.master.onboarding import get_language_kb, get_master_menu_kb

router = Router()


def format_profile_text(master, language: str) -> str:
    phone = master.phone or ("Kiritilmagan" if language == "uz" else "Не указан")
    if language == "uz":
        return (
            f"👤 Ism: {master.full_name}\n"
            f"📱 Telefon: {phone}\n"
            f"🏢 Salon ID: {master.salon_id}"
        )
    else:
        return (
            f"👤 Имя: {master.full_name}\n"
            f"📱 Телефон: {phone}\n"
            f"🏢 ID салона: {master.salon_id}"
        )


@router.message(F.text.in_(["👤 Profil", "👤 Профиль"]))
async def show_profile(message: Message):
    master = await get_master_by_telegram_id(message.from_user.id)
    if master is None:
        return

    text = format_profile_text(master, master.language)
    change_lang_text = (
        "🌐 Tilni o'zgartirish" if master.language == "uz" else "🌐 Изменить язык"
    )
    text += (
        f"\n\n{change_lang_text} - pastgdagi tugmadan foydalaning"
        if master.language == "uz"
        else f"\n\n{change_lang_text} - используйте кнопку ниже"
    )
    await message.answer(text, reply_markup=get_language_kb())


@router.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский"]))
async def change_language(message: Message):
    master = await get_master_by_telegram_id(message.from_user.id)
    if master is None:
        return

    new_language = "uz" if "O'zbekcha" in message.text else "ru"
    await update_master_language(master.id, new_language)

    text = "Til o'zgartirildi ✅" if new_language == "uz" else "Язык изменён ✅"
    await message.answer(text, reply_markup=get_master_menu_kb(new_language))
