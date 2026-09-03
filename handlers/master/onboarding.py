
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.repositories.salon_repo import (
    get_master_by_phone,
    link_master_telegram,
    update_master_language,
)

router = Router()


class MasterOnboardingStates(StatesGroup):
    choosing_language = State()
    waiting_for_phone = State()


def get_language_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 O'zbekcha"),
                KeyboardButton(text="🇷🇺 Русский"),
            ]
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
        keyboard=[
            [KeyboardButton(text=text, request_contact=True)]
        ],
        resize_keyboard=True,
    )


def get_add_salon_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    text = (
        "🏢 Salon qo'shish"
        if language == "uz"
        else "🏢 Добавить салон"
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text)]
        ],
        resize_keyboard=True,
    )


def get_master_menu_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    if language == "uz":
        buttons = [
            [KeyboardButton(text="📅 Bugungi grafik")],
            [KeyboardButton(text="⏳ Vaqtni yopish")],
            [KeyboardButton(text="👤 Profil")],
        ]
    else:
        buttons = [
            [KeyboardButton(text="📅 Расписание на сегодня")],
            [KeyboardButton(text="⏳ Закрыть время")],
            [KeyboardButton(text="👤 Профиль")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(
        MasterOnboardingStates.choosing_language
    )

    await message.answer(
        "Tilni tanlang / Выберите язык:",
        reply_markup=get_language_kb(),
    )


@router.message(
    MasterOnboardingStates.choosing_language,
    F.text.in_([
        "🇺🇿 O'zbekcha",
        "🇷🇺 Русский",
    ]),
)
async def language_chosen(
    message: Message,
    state: FSMContext,
):
    language = (
        "uz"
        if message.text == "🇺🇿 O'zbekcha"
        else "ru"
    )

    await state.update_data(language=language)

    await state.set_state(
        MasterOnboardingStates.waiting_for_phone
    )

    text = (
        "Tizimga kirish uchun telefon raqamingizni tasdiqlang:"
        if language == "uz"
        else
        "Подтвердите номер телефона для входа в систему:"
    )

    await message.answer(
        text,
        reply_markup=get_phone_kb(language),
    )


@router.message(
    MasterOnboardingStates.waiting_for_phone,
    F.contact,
)
async def phone_received(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    language = data.get("language", "uz")

    phone = message.contact.phone_number

    if not phone.startswith("+"):
        phone = "+" + phone

    # Master bazadan qidiriladi
    master = await get_master_by_phone(phone)

    # ==========================================
    # MASTER RO'YXATDA YO'Q
    # ==========================================
    if master is None:
        text = (
            "❌ Siz tizimda master sifatida ro'yxatdan o'tmagansiz.\n\n"
            "Iltimos, administratorlar bilan bog'laning."
            if language == "uz"
            else
            "❌ Вы не зарегистрированы в системе как мастер.\n\n"
            "Пожалуйста, свяжитесь с администраторами."
        )

        await message.answer(
            text,
        )

        # Onboarding tugadi
        await state.clear()

        return

    # ==========================================
    # MASTER RO'YXATDA BOR
    # ==========================================

    # Telegram accountni masterga bog'lash
    await link_master_telegram(
        master.id,
        message.from_user.id,
    )

    # Tanlangan tilni saqlash
    await update_master_language(
        master.id,
        language,
    )

    if master.salon_id is not None:
        text = (
            f"✅ Xush kelibsiz, {master.full_name}!"
            if language == "uz"
            else f"✅ Добро пожаловать, {master.full_name}!"
        )
        await message.answer(text, reply_markup=get_master_menu_kb(language))
    else:
        text = (
            f"✅ Xush kelibsiz, {master.full_name}!\n\nSalon qo'shmoqchimisiz?"
            if language == "uz"
            else f"✅ Добро пожаловать, {master.full_name}!\n\nХотите добавить салон?"
        )
        await message.answer(text, reply_markup=get_add_salon_kb(language))

    # Endi master salon qo'shish bosqichida
    await state.clear()


@router.message(
    MasterOnboardingStates.waiting_for_phone
)
async def phone_not_received(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    language = data.get("language", "uz")

    text = (
        "Iltimos, tugma orqali telefon raqamingizni yuboring 📱"
        if language == "uz"
        else
        "Пожалуйста, отправьте номер телефона через кнопку 📱"
    )

    await message.answer(text)

