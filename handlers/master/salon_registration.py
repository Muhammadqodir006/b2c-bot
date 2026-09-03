from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from config import settings
from database.repositories.salon_repo import create_pending_salon, approve_salon, reject_salon, get_salon, link_master_to_salon, get_salon_by_owner, get_all_categories, create_service

router = Router()

master_bot = Bot(token=settings.master_bot_token)


class SalonRegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()
    waiting_for_location = State()
    confirming = State()


def get_location_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    text = "📍 Joylashuvni yuborish" if language == "uz" else "📍 Отправить геолокацию"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_location=True)]],
        resize_keyboard=True,
    )


def get_confirm_kb(language: str = "uz") -> InlineKeyboardMarkup:
    yes = "✅ Ha" if language == "uz" else "✅ Да"
    no = "❌ Yo'q" if language == "uz" else "❌ Нет"
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=yes, callback_data="salon_reg_confirm"),
            InlineKeyboardButton(text=no, callback_data="salon_reg_cancel"),
        ]]
    )


def get_admin_review_kb(salon_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_salon:{salon_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_salon:{salon_id}"),
        ]]
    )
    
def get_add_service_kb(language: str = "uz"):
    text = "💈 Xizmat qo'shish" if language == "uz" else "💈 Добавить услугу"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text)]],
        resize_keyboard=True,
    )


@router.message(F.text.in_(["🏢 Salon qo'shish", "🏢 Добавить салон"]))
async def start_salon_registration(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await state.set_state(SalonRegistrationStates.waiting_for_name)
    text = "Salon nomini kiriting:" if language == "uz" else "Введите название салона:"
    await message.answer(text, reply_markup=ReplyKeyboardRemove())


@router.message(SalonRegistrationStates.waiting_for_name, F.text)
async def salon_name_received(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await state.update_data(salon_name=message.text.strip())
    await state.set_state(SalonRegistrationStates.waiting_for_address)

    text = "Manzilni kiriting:" if language == "uz" else "Введите адрес:"
    await message.answer(text)


@router.message(SalonRegistrationStates.waiting_for_address, F.text)
async def salon_address_received(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await state.update_data(salon_address=message.text.strip())
    await state.set_state(SalonRegistrationStates.waiting_for_location)

    text = "Endi joylashuvni yuboring:" if language == "uz" else "Теперь отправьте геолокацию:"
    await message.answer(text, reply_markup=get_location_kb(language))


@router.message(SalonRegistrationStates.waiting_for_location, F.location)
async def salon_location_received(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude,
    )
    await state.set_state(SalonRegistrationStates.confirming)

    data = await state.get_data()
    text = (
        f"🏢 {data['salon_name']}\n📍 {data['salon_address']}\n\nTasdiqlaysizmi?"
        if language == "uz"
        else f"🏢 {data['salon_name']}\n📍 {data['salon_address']}\n\nПодтверждаете?"
    )
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await message.answer("⬇️", reply_markup=get_confirm_kb(language))


@router.callback_query(SalonRegistrationStates.confirming, F.data == "salon_reg_confirm")
async def confirm_salon_registration(callback, state: FSMContext):
    data = await state.get_data()
    language = data.get("language", "uz")

    salon = await create_pending_salon(
        name=data["salon_name"],
        address=data["salon_address"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        owner_telegram_id=callback.from_user.id,
    )

    await state.clear()

    text = (
        "✅ So'rovingiz yuborildi! Admin tasdiqlagach, botdan foydalana olasiz."
        if language == "uz"
        else "✅ Ваш запрос отправлен! После подтверждения администратором вы сможете пользоваться ботом."
    )
    await callback.message.edit_text(text)
    await callback.answer()

    admin_text = (
        f"🆕 Yangi salon so'rovi:\n"
        f"🏢 {salon.name}\n"
        f"📍 {salon.address}\n"
        f"👤 Egasi ID: {salon.owner_telegram_id}"
    )
    for admin_id in settings.admin_id_list:
        await master_bot.send_message(
            chat_id=admin_id, text=admin_text, reply_markup=get_admin_review_kb(salon.id)
        )


@router.callback_query(SalonRegistrationStates.confirming, F.data == "salon_reg_cancel")
async def cancel_salon_registration(callback, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data.startswith("approve_salon:"))
async def handle_approve_salon(callback):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    salon_id = int(callback.data.split(":")[1])
    salon = await approve_salon(salon_id)

    if salon is None:
        await callback.answer("Salon topilmadi.", show_alert=True)
        return

    if salon.owner_telegram_id:
        master = await link_master_to_salon(salon.owner_telegram_id, salon.id)
        master_lang = master.language if master else "uz"
    else:
        master_lang = "uz"

    await callback.message.edit_text(callback.message.text + "\n\n✅ TASDIQLANDI")
    await callback.answer()

    if salon.owner_telegram_id:
        text = (
            f"🎉 Saloningiz '{salon.name}' tasdiqlandi!\n\nEndi kamida bitta xizmat qo'shing:"
            if master_lang == "uz"
            else f"🎉 Ваш салон '{salon.name}' подтверждён!\n\nТеперь добавьте хотя бы одну услугу:"
        )
        await master_bot.send_message(
            chat_id=salon.owner_telegram_id,
            text=text,
            reply_markup=get_add_service_kb(master_lang),
        )

@router.callback_query(F.data.startswith("reject_salon:"))
async def handle_reject_salon(callback):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    salon_id = int(callback.data.split(":")[1])
    salon = await get_salon(salon_id)
    owner_id = salon.owner_telegram_id if salon else None

    await reject_salon(salon_id)

    await callback.message.edit_text(callback.message.text + "\n\n❌ RAD ETILDI")
    await callback.answer()

    if owner_id:
        await master_bot.send_message(
            chat_id=owner_id,
            text="😔 Salon so'rovingiz rad etildi. Qo'shimcha ma'lumot uchun admin bilan bog'laning."
        )
        
class OwnerAddServiceStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_duration = State()
    waiting_for_category = State()


def get_category_kb(categories, language: str = "uz"):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat.name, callback_data=f"owner_cat:{cat.id}")
    builder.adjust(1)
    return builder.as_markup()


@router.message(F.text.in_(["💈 Xizmat qo'shish", "💈 Добавить услугу"]))
async def start_owner_add_service(message: Message, state: FSMContext):
    salon = await get_salon_by_owner(message.from_user.id)
    if salon is None:
        return

    await state.update_data(owner_salon_id=salon.id)
    await state.set_state(OwnerAddServiceStates.waiting_for_name)
    await message.answer("Xizmat nomini kiriting:", reply_markup=ReplyKeyboardRemove())


@router.message(OwnerAddServiceStates.waiting_for_name, F.text)
async def owner_service_name(message: Message, state: FSMContext):
    await state.update_data(service_name=message.text.strip())
    await state.set_state(OwnerAddServiceStates.waiting_for_price)
    await message.answer("Narxini kiriting (so'mda, faqat raqam):")


@router.message(OwnerAddServiceStates.waiting_for_price, F.text)
async def owner_service_price(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Narx raqam bo'lishi kerak. Qaytadan kiriting:")
        return
    await state.update_data(service_price=int(message.text.strip()))
    await state.set_state(OwnerAddServiceStates.waiting_for_duration)
    await message.answer("Davomiyligini kiriting (daqiqada, masalan 45):")


@router.message(OwnerAddServiceStates.waiting_for_duration, F.text)
async def owner_service_duration(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Davomiylik raqam bo'lishi kerak. Qaytadan kiriting:")
        return
    await state.update_data(service_duration=int(message.text.strip()))

    from database.repositories.salon_repo import get_all_categories
    categories = await get_all_categories()
    if not categories:
        await message.answer("Bazada kategoriyalar yo'q. Admin bilan bog'laning.")
        await state.clear()
        return

    await state.set_state(OwnerAddServiceStates.waiting_for_category)
    await message.answer("Kategoriyani tanlang:", reply_markup=get_category_kb(categories))


@router.callback_query(OwnerAddServiceStates.waiting_for_category, F.data.startswith("owner_cat:"))
async def owner_service_category(callback, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    from database.repositories.salon_repo import create_service
    await create_service(
        salon_id=data["owner_salon_id"],
        category_id=category_id,
        name=data["service_name"],
        price=data["service_price"],
        duration_minutes=data["service_duration"],
    )

    await state.clear()
    await callback.message.edit_text("✅ Xizmat qo'shildi! Endi /start bosing.")
    await callback.answer()