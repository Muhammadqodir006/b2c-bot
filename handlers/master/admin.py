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
)

from config import settings
from database.repositories.salon_repo import get_all_salons, get_salon, create_master

router = Router()


class AddMasterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_salon_id = State()
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
    await message.answer(
        "Telefon raqamini kiriting (masalan: +998901234567):"
    )


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
        await message.answer(
            f"ID {salon_id} bilan salon topilmadi. Qaytadan kiriting:"
        )
        return

    await state.update_data(salon_id=salon_id, salon_name=salon.name)
    await state.set_state(AddMasterStates.confirming)

    data = await state.get_data()
    text = (
        f"{data['full_name']}, {data['phone']}, Salon: {data['salon_name']} — to'g'rimi?"
    )
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