from aiogram import Router, F
from aiogram.types import Message
from database.repositories.user_repo import get_user, update_language
from handlers.client.onboarding import get_language_kb
from keyboards.client.main_kb import get_main_menu_kb
from services.referral_service import create_referral_code_for_user
from services.points_service import get_user_points
from config import settings

router = Router()

BOT_USERNAME = "salon_b2c_bot"  # o'zingizning bot username'ingizga moslang


async def format_profile_text(user, language: str) -> str:
    phone = user.phone or ("Kiritilmagan" if language == "uz" else "Не указан")

    referral_code = await create_referral_code_for_user(user.id)
    points = await get_user_points(user.id)
    referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code.code}"

    if language == "uz":
        return (
            f"👤 Ism: {user.full_name}\n"
            f"📱 Telefon: {phone}\n"
            f"⭐️ Ishonchlilik balli: {user.trust_score}\n"
            f"🏆 Ballaringiz: {points}\n\n"
            f"🔗 Do'stlaringizni taklif qiling:\n{referral_link}"
        )
    else:
        return (
            f"👤 Имя: {user.full_name}\n"
            f"📱 Телефон: {phone}\n"
            f"⭐️ Рейтинг доверия: {user.trust_score}\n"
            f"🏆 Баллы: {points}\n\n"
            f"🔗 Пригласите друзей:\n{referral_link}"
        )


@router.message(F.text.in_(["👤 Shaxsiy kabinet", "👤 Личный кабинет"]))
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if user is None:
        return

    text = await format_profile_text(user, user.language)
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