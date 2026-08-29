from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.repositories.user_repo import (
    get_or_create_user,
    update_phone,
    update_language,
)
from keyboards.client.main_kb import get_main_menu_kb
from services.referral_service import get_user_by_referral_code, create_referral

router = Router()


class OnboardingStates(StatesGroup):
    choosing_language = State()
    waiting_for_phone = State()


def get_language_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
        ],
        resize_keyboard=True,
    )


def get_phone_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    text = (
        "📱 Telefon raqamni yuborish"
        if language == "uz"
        else "📱 Отправить номер телефона"
    )
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_contact=True)]],
        resize_keyboard=True,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        referral_code = args[1].strip()

        referrer = await get_user_by_referral_code(referral_code)

        if referrer and referrer.telegram_id != message.from_user.id:
            referred_user = await get_or_create_user(
                telegram_id=message.from_user.id,
                full_name=message.from_user.full_name,
            )

            await create_referral(
                referrer_id=referrer.id,
                referred_id=referred_user.id,
            )

    await state.set_state(OnboardingStates.choosing_language)

    await message.answer(
        "Tilni tanlang / Выберите язык:",
        reply_markup=get_language_kb(),
    )


@router.message(
    OnboardingStates.choosing_language, F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский"])
)
async def language_chosen(message: Message, state: FSMContext):
    language = "uz" if "O'zbekcha" in message.text else "ru"
    await state.update_data(language=language)
    await state.set_state(OnboardingStates.waiting_for_phone)

    text = (
        "Telefon raqamingizni tasdiqlang:"
        if language == "uz"
        else "Подтвердите номер телефона:"
    )
    await message.answer(text, reply_markup=get_phone_kb(language))


@router.message(OnboardingStates.waiting_for_phone, F.contact)
async def phone_received(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
    )
    await update_phone(
        telegram_id=message.from_user.id, phone=message.contact.phone_number
    )
    await update_language(telegram_id=message.from_user.id, language=language)

    await state.clear()

    text = "Xush kelibsiz! 🎉" if language == "uz" else "Добро пожаловать! 🎉"
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await message.answer(
        "Asosiy menyu:" if language == "uz" else "Главное меню:",
        reply_markup=get_main_menu_kb(language),
    )


@router.message(OnboardingStates.waiting_for_phone)
async def phone_not_received(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")
    text = (
        "Iltimos, tugma orqali telefon raqamingizni yuboring 📱"
        if language == "uz"
        else "Пожалуйста, отправьте номер телефона через кнопку 📱"
    )
    await message.answer(text)
