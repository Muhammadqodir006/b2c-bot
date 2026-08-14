from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import settings
from database.repositories.salon_repo import (
    get_all_salons,
    get_salon,
    create_master,
    create_salon,
    create_service,
    get_all_categories,
)

router = Router()


class AddMasterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_salon_id = State()
    confirming = State()


class AddSalonStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()
    waiting_for_location = State()
    confirming = State()


class AddServiceStates(StatesGroup):
    waiting_for_salon_id = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_duration = State()
    waiting_for_category_id = State()
    confirming = State()


def get_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data="add_master_confirm"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="add_master_cancel"),
            ]
        ]
    )


def get_add_salon_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha",
                    callback_data="add_salon_confirm",
                ),
                InlineKeyboardButton(
                    text="❌ Yo'q",
                    callback_data="add_salon_cancel",
                ),
            ]
        ]
    )


def get_location_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📍 Lokatsiyani yuborish",
                    request_location=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_add_service_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha",
                    callback_data="add_service_confirm",
                ),
                InlineKeyboardButton(
                    text="❌ Yo'q",
                    callback_data="add_service_cancel",
                ),
            ]
        ]
    )


def normalize_phone(raw: str) -> str:
    phone = raw.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


@router.message(Command("add_master"))
async def start_add_master(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_id_list:
        await message.answer("Bu buyruq faqat administratorlar uchun.")
        return

    await state.set_state(AddMasterStates.waiting_for_name)
    await message.answer(
        "Yangi ustaning ism-familiyasini kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AddMasterStates.waiting_for_name, F.text)
async def name_received(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if not full_name:
        await message.answer("Ism-familiyani matn ko'rinishida kiriting:")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(AddMasterStates.waiting_for_phone)
    await message.answer("Telefon raqamini kiriting (masalan: +998901234567):")


@router.message(AddMasterStates.waiting_for_name)
async def name_not_received(message: Message, state: FSMContext):
    await message.answer("Iltimos, ism-familiyani matn ko'rinishida kiriting:")


@router.message(AddMasterStates.waiting_for_phone, F.text)
async def phone_received(message: Message, state: FSMContext):
    phone = normalize_phone(message.text)

    if not phone[1:].isdigit() or len(phone) < 10:
        await message.answer(
            "Telefon raqami noto'g'ri ko'rinishda. Qaytadan kiriting (masalan: +998901234567):"
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(AddMasterStates.waiting_for_salon_id)

    salons = await get_all_salons()
    if salons:
        salon_list = "\n".join(f"ID {s.id} — {s.name}" for s in salons)
        text = f"Mavjud salonlar:\n{salon_list}\n\nUsta biriktiriladigan salon ID sini kiriting:"
    else:
        text = "Hozircha bazada salonlar yo'q. Usta biriktiriladigan salon ID sini kiriting:"

    await message.answer(text)


@router.message(AddMasterStates.waiting_for_phone)
async def phone_not_received(message: Message, state: FSMContext):
    await message.answer(
        "Iltimos, telefon raqamini matn ko'rinishida kiriting (masalan: +998901234567):"
    )


@router.message(AddMasterStates.waiting_for_salon_id, F.text)
async def salon_id_received(message: Message, state: FSMContext):
    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer("Salon ID raqam bo'lishi kerak. Qaytadan kiriting:")
        return

    salon_id = int(raw)
    salon = await get_salon(salon_id)
    if salon is None:
        await message.answer(f"ID {salon_id} bilan salon topilmadi. Qaytadan kiriting:")
        return

    await state.update_data(salon_id=salon_id, salon_name=salon.name)
    await state.set_state(AddMasterStates.confirming)

    data = await state.get_data()
    text = f"{data['full_name']}, {data['phone']}, Salon: {data['salon_name']} — to'g'rimi?"
    await message.answer(text, reply_markup=get_confirm_kb())


@router.message(AddMasterStates.waiting_for_salon_id)
async def salon_id_not_received(message: Message, state: FSMContext):
    await message.answer("Iltimos, salon ID sini raqam ko'rinishida kiriting:")


@router.callback_query(AddMasterStates.confirming, F.data == "add_master_confirm")
async def confirm_add_master(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    master = await create_master(
        salon_id=data["salon_id"],
        full_name=data["full_name"],
        phone=data["phone"],
    )

    await state.clear()
    await callback.message.edit_text(
        f"✅ Yangi usta qo'shildi: {master.full_name} ({master.phone})."
    )
    await callback.answer()


@router.callback_query(AddMasterStates.confirming, F.data == "add_master_cancel")
async def cancel_add_master(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi. Usta qo'shilmadi.")
    await callback.answer()


@router.message(Command("add_salon"))
async def start_add_salon(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_id_list:
        await message.answer("Bu buyruq faqat administratorlar uchun.")
        return

    await state.set_state(AddSalonStates.waiting_for_name)
    await message.answer(
        "Yangi salon nomini kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AddSalonStates.waiting_for_name, F.text)
async def salon_name_received(message: Message, state: FSMContext):
    name = message.text.strip()

    if not name:
        await message.answer("Salon nomini matn ko'rinishida kiriting:")
        return

    await state.update_data(name=name)
    await state.set_state(AddSalonStates.waiting_for_address)

    await message.answer("Salon manzilini kiriting:")


@router.message(AddSalonStates.waiting_for_name)
async def salon_name_not_received(message: Message, state: FSMContext):
    await message.answer("Iltimos, salon nomini matn ko'rinishida kiriting:")


@router.message(AddSalonStates.waiting_for_address, F.text)
async def salon_address_received(message: Message, state: FSMContext):
    address = message.text.strip()

    if not address:
        await message.answer("Salon manzilini kiriting:")
        return

    await state.update_data(address=address)
    await state.set_state(AddSalonStates.waiting_for_location)

    await message.answer(
        "Salon joylashuvini yuboring:",
        reply_markup=get_location_kb(),
    )


@router.message(AddSalonStates.waiting_for_address)
async def salon_address_not_received(message: Message, state: FSMContext):
    await message.answer("Iltimos, manzilni matn ko'rinishida kiriting:")


@router.message(AddSalonStates.waiting_for_location, F.location)
async def salon_location_received(message: Message, state: FSMContext):
    location = message.location

    await state.update_data(
        latitude=location.latitude,
        longitude=location.longitude,
    )

    await state.set_state(AddSalonStates.confirming)

    data = await state.get_data()

    text = (
        f"Salon ma'lumotlari:\n\n"
        f"🏪 Nomi: {data['name']}\n"
        f"📍 Manzil: {data['address']}\n"
        f"🌐 Latitude: {data['latitude']}\n"
        f"🌐 Longitude: {data['longitude']}\n\n"
        f"Ma'lumotlar to'g'rimi?"
    )

    await message.answer(
        text,
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        "Tasdiqlaysizmi?",
        reply_markup=get_add_salon_confirm_kb(),
    )


@router.message(AddSalonStates.waiting_for_location)
async def salon_location_not_received(message: Message, state: FSMContext):
    await message.answer(
        "Iltimos, pastdagi tugma orqali salon lokatsiyasini yuboring:",
        reply_markup=get_location_kb(),
    )


@router.callback_query(
    AddSalonStates.confirming,
    F.data == "add_salon_confirm",
)
async def confirm_add_salon(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    salon = await create_salon(
        name=data["name"],
        address=data["address"],
        latitude=data["latitude"],
        longitude=data["longitude"],
    )

    await state.clear()

    await callback.message.edit_text(f"✅ Yangi salon qo'shildi: {salon.name}")
    await callback.answer()


@router.callback_query(
    AddSalonStates.confirming,
    F.data == "add_salon_cancel",
)
async def cancel_add_salon(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.edit_text("❌ Bekor qilindi. Salon qo'shilmadi.")
    await callback.answer()


@router.message(Command("add_service"))
async def start_add_service(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_id_list:
        await message.answer("Bu buyruq faqat administratorlar uchun.")
        return

    salons = await get_all_salons()

    if not salons:
        await message.answer("Hozircha bazada salonlar yo'q.")
        return

    salon_list = "\n".join(f"ID {salon.id} — {salon.name}" for salon in salons)

    await state.set_state(AddServiceStates.waiting_for_salon_id)

    await message.answer(
        f"Mavjud salonlar:\n{salon_list}\n\n"
        f"Xizmat qo'shiladigan salon ID sini kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AddServiceStates.waiting_for_salon_id, F.text)
async def service_salon_id_received(
    message: Message,
    state: FSMContext,
):
    raw = message.text.strip()

    if not raw.isdigit():
        await message.answer("Salon ID raqam bo'lishi kerak. Qaytadan kiriting:")
        return

    salon_id = int(raw)

    salon = await get_salon(salon_id)

    if salon is None:
        await message.answer(f"ID {salon_id} bilan salon topilmadi. Qaytadan kiriting:")
        return

    await state.update_data(
        salon_id=salon_id,
        salon_name=salon.name,
    )

    await state.set_state(AddServiceStates.waiting_for_name)

    await message.answer("Xizmat nomini kiriting:")


@router.message(AddServiceStates.waiting_for_salon_id)
async def service_salon_id_not_received(
    message: Message,
    state: FSMContext,
):
    await message.answer("Iltimos, salon ID sini raqam ko'rinishida kiriting:")


@router.message(AddServiceStates.waiting_for_name, F.text)
async def service_name_received(
    message: Message,
    state: FSMContext,
):
    name = message.text.strip()

    if not name:
        await message.answer("Xizmat nomini kiriting:")
        return

    await state.update_data(name=name)
    await state.set_state(AddServiceStates.waiting_for_price)

    await message.answer("Xizmat narxini kiriting:")


@router.message(AddServiceStates.waiting_for_name)
async def service_name_not_received(
    message: Message,
    state: FSMContext,
):
    await message.answer("Iltimos, xizmat nomini matn ko'rinishida kiriting:")


@router.message(AddServiceStates.waiting_for_price, F.text)
async def service_price_received(
    message: Message,
    state: FSMContext,
):
    raw = message.text.strip()

    if not raw.isdigit():
        await message.answer("Narx raqam bo'lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(price=int(raw))
    await state.set_state(AddServiceStates.waiting_for_duration)

    await message.answer("Xizmat davomiyligini daqiqada kiriting:")


@router.message(AddServiceStates.waiting_for_price)
async def service_price_not_received(
    message: Message,
    state: FSMContext,
):
    await message.answer("Iltimos, narxni raqam ko'rinishida kiriting:")


@router.message(AddServiceStates.waiting_for_duration, F.text)
async def service_duration_received(
    message: Message,
    state: FSMContext,
):
    raw = message.text.strip()

    if not raw.isdigit():
        await message.answer("Davomiylik raqam bo'lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(duration_minutes=int(raw))
    await state.set_state(AddServiceStates.waiting_for_category_id)

    categories = await get_all_categories()

    if not categories:
        await message.answer("Hozircha kategoriyalar mavjud emas.")
        await state.clear()
        return

    category_list = "\n".join(
        f"ID {category.id} — {category.name}" for category in categories
    )

    await message.answer(
        f"Mavjud kategoriyalar:\n{category_list}\n\nKategoriya ID sini kiriting:"
    )


@router.message(AddServiceStates.waiting_for_duration)
async def service_duration_not_received(
    message: Message,
    state: FSMContext,
):
    await message.answer("Iltimos, davomiylikni raqam ko'rinishida kiriting:")


@router.message(
    AddServiceStates.waiting_for_category_id,
    F.text,
)
async def service_category_id_received(
    message: Message,
    state: FSMContext,
):
    raw = message.text.strip()

    if not raw.isdigit():
        await message.answer("Kategoriya ID raqam bo'lishi kerak. Qaytadan kiriting:")
        return

    category_id = int(raw)

    categories = await get_all_categories()
    category = next(
        (category for category in categories if category.id == category_id),
        None,
    )

    if category is None:
        await message.answer(
            f"ID {category_id} bilan kategoriya topilmadi. Qaytadan kiriting:"
        )
        return

    await state.update_data(
        category_id=category_id,
        category_name=category.name,
    )

    await state.set_state(AddServiceStates.confirming)

    data = await state.get_data()

    text = (
        f"Xizmat ma'lumotlari:\n\n"
        f"🏪 Salon: {data['salon_name']}\n"
        f"🛠 Xizmat: {data['name']}\n"
        f"💰 Narx: {data['price']}\n"
        f"⏱ Davomiyligi: {data['duration_minutes']} daqiqa\n"
        f"📂 Kategoriya: {data['category_name']}\n\n"
        f"Ma'lumotlar to'g'rimi?"
    )

    await message.answer(
        text,
        reply_markup=get_add_service_confirm_kb(),
    )


@router.message(AddServiceStates.waiting_for_category_id)
async def service_category_id_not_received(
    message: Message,
    state: FSMContext,
):
    await message.answer("Iltimos, kategoriya ID sini raqam ko'rinishida kiriting:")


@router.callback_query(
    AddServiceStates.confirming,
    F.data == "add_service_confirm",
)
async def confirm_add_service(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()

    service = await create_service(
        salon_id=data["salon_id"],
        category_id=data["category_id"],
        name=data["name"],
        price=data["price"],
        duration_minutes=data["duration_minutes"],
    )

    await state.clear()

    await callback.message.edit_text(f"✅ Yangi xizmat qo'shildi: {service.name}")
    await callback.answer()


@router.callback_query(
    AddServiceStates.confirming,
    F.data == "add_service_cancel",
)
async def cancel_add_service(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text("❌ Bekor qilindi. Xizmat qo'shilmadi.")
    await callback.answer()
