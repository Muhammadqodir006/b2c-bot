from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from database.repositories.user_repo import get_user
from database.repositories.salon_repo import get_all_salons
from services.geo_service import get_nearby_salons
from services.salon_service import get_salons_by_category
from keyboards.client.main_kb import get_main_menu_kb
from aiogram.fsm.context import FSMContext
from states.booking_states import BookingStates

router = Router()


class CategoryCallback(CallbackData, prefix="category"):
    category_id: int


def get_location_request_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    text = "📍 Joylashuvni yuborish" if language == "uz" else "📍 Отправить геолокацию"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_location=True)]],
        resize_keyboard=True,
    )


def _category_keyboard(categories: list, language: str):
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category.name,
            callback_data=CategoryCallback(category_id=category.id).pack(),
        )
    builder.adjust(1)
    return builder.as_markup()


@router.message(F.text.in_(["📍 Yaqin atrofdagi salonlar", "📍 Салоны рядом"]))
async def nearby_salons_request(message: Message):
    user = await get_user(message.from_user.id)
    lang = user.language if user else "uz"

    text = (
        "Joylashuvingizni yuboring, yaqin atrofdagi salonlarni topamiz:"
        if lang == "uz"
        else "Отправьте геолокацию, найдём салоны рядом с вами:"
    )
    await message.answer(text, reply_markup=get_location_request_kb(lang))


@router.message(F.location)
async def nearby_salons_result(message: Message):
    user = await get_user(message.from_user.id)
    lang = user.language if user else "uz"

    nearby = await get_nearby_salons(
        message.location.latitude,
        message.location.longitude,
    )

    if not nearby:
        text = (
            "Yaqin atrofda salon topilmadi 😔"
            if lang == "uz"
            else "Поблизости салоны не найдены 😔"
        )
        await message.answer(text, reply_markup=get_main_menu_kb(lang))
        return

    lines = []
    for salon, distance in nearby:
        lines.append(f"🏢 {salon.name} — {distance:.1f} km")

    header = (
        "📍 Yaqin atrofdagi salonlar:\n\n" if lang == "uz" else "📍 Салоны рядом:\n\n"
    )
    await message.answer(header + "\n".join(lines), reply_markup=get_main_menu_kb(lang))


@router.message(F.text.in_(["🔍 Kategoriyalar", "🔍 Категории"]))
async def show_categories(message: Message):
    from database.engine import async_session
    from database.models import Category
    from sqlalchemy import select

    user = await get_user(message.from_user.id)
    lang = user.language if user else "uz"

    async with async_session() as session:
        result = await session.execute(select(Category))
        categories = list(result.scalars().all())

    if not categories:
        text = (
            "Kategoriyalar hali qo'shilmagan."
            if lang == "uz"
            else "Категории пока не добавлены."
        )
        await message.answer(text)
        return

    text = "Kategoriyani tanlang:" if lang == "uz" else "Выберите категорию:"
    await message.answer(text, reply_markup=_category_keyboard(categories, lang))


@router.callback_query(CategoryCallback.filter())
async def category_selected(callback, callback_data: CategoryCallback):
    user = await get_user(callback.from_user.id)
    lang = user.language if user else "uz"

    salons = await get_salons_by_category(callback_data.category_id)

    if not salons:
        text = (
            "Bu kategoriyada salon topilmadi."
            if lang == "uz"
            else "В этой категории салонов нет."
        )
        await callback.message.answer(text)
        await callback.answer()
        return

    lines = [f"🏢 {salon.name} — {salon.address}" for salon in salons]
    header = "Topilgan salonlar:\n\n" if lang == "uz" else "Найденные салоны:\n\n"
    await callback.message.answer(header + "\n".join(lines))
    await callback.answer()


@router.message(F.text.in_(["📅 Bron qilish", "📅 Записаться"]))
async def start_booking_from_menu(message: Message, state: FSMContext):
    from database.repositories.salon_repo import get_all_salons
    from keyboards.client.booking_kb import salons_keyboard

    salons = await get_all_salons()
    if not salons:
        await message.answer("Hozircha salonlar mavjud emas.")
        return

    await state.set_state(BookingStates.choosing_salon)
    await message.answer("🏢 Salonni tanlang:", reply_markup=salons_keyboard(salons))
