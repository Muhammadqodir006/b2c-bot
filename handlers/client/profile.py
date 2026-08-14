from aiogram import Router, F
from aiogram.types import Message

from database.repositories.user_repo import get_user, update_language
from handlers.client.onboarding import get_language_kb
from keyboards.client.main_kb import get_main_menu_kb

router = Router()


def format_profile_text(user, language: str) -> str:
    phone = user.phone or ("Kiritilmagan" if language == "uz" else "Не указан")
    if language == "uz":
        return (
            f"👤 Ism: {user.full_name}\n"
            f"📱 Telefon: {phone}\n"
            f"⭐️ Ishonchlilik balli: {user.trust_score}"
        )
    else:
        return (
            f"👤 Имя: {user.full_name}\n"
            f"📱 Телефон: {phone}\n"
            f"⭐️ Рейтинг доверия: {user.trust_score}"
        )


@router.message(F.text.in_(["👤 Shaxsiy kabinet", "👤 Личный кабинет"]))
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if user is None:
        return

    text = format_profile_text(user, user.language)
    change_lang_text = (
        "🌐 Tilni o'zgartirish" if user.language == "uz" else "🌐 Изменить язык"
    )
    text += (
        f"\n\n{change_lang_text} — pastdagi tugmadan foydalaning"
        if user.language == "uz"
        else f"\n\n{change_lang_text} — используйте кнопку ниже"
    )

    await message.answer(text, reply_markup=get_language_kb())


@router.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский"]))
async def change_language(message: Message):
    user = await get_user(message.from_user.id)
    if user is None:
        return

    new_language = "uz" if "O'zbekcha" in message.text else "ru"
    updated_user = await update_language(message.from_user.id, new_language)

    text = "Til o'zgartirildi ✅" if new_language == "uz" else "Язык изменён ✅"
    await message.answer(text, reply_markup=get_main_menu_kb(new_language))
