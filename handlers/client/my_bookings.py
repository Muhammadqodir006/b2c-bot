from datetime import timedelta
from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from database.engine import async_session
from database.models import BookingStatus, Salon, Service
from database.repositories import booking_repo, user_repo
from services.time_service import to_local, now_utc

router = Router(name="client_my_bookings")

ACTIVE_STATUSES = (BookingStatus.pending, BookingStatus.confirmed)
CANCEL_MIN_HOURS = 2

STATUS_LABELS = {
    "uz": {
        BookingStatus.pending: "⏳ Kutilmoqda",
        BookingStatus.confirmed: "✅ Tasdiqlangan",
        BookingStatus.completed: "🏁 Yakunlangan",
        BookingStatus.cancelled: "❌ Bekor qilingan",
        BookingStatus.no_show: "🚫 Kelmagan",
    },
    "ru": {
        BookingStatus.pending: "⏳ Ожидается",
        BookingStatus.confirmed: "✅ Подтверждено",
        BookingStatus.completed: "🏁 Завершено",
        BookingStatus.cancelled: "❌ Отменено",
        BookingStatus.no_show: "🚫 Не пришёл",
    },
}

class BookingCancelCallback(CallbackData, prefix="bk_cancel"):
    booking_id: int

async def _load_salons_and_services(bookings: list) -> tuple[dict, dict]:
    if not bookings:
        return {}, {}

    salon_ids = {b.salon_id for b in bookings}
    service_ids = {b.service_id for b in bookings}

    async with async_session() as session:
        salons_res = await session.execute(select(Salon).where(Salon.id.in_(salon_ids)))
        services_res = await session.execute(select(Service).where(Service.id.in_(service_ids)))
        salons = {s.id: s for s in salons_res.scalars().all()}
        services = {s.id: s for s in services_res.scalars().all()}

    return salons, services

def _format_booking(booking, salons: dict, services: dict, language: str) -> str:
    salon = salons.get(booking.salon_id)
    service = services.get(booking.service_id)

    salon_name = salon.name if salon else "—"
    service_name = service.name if service else "—"
    when = to_local(booking.scheduled_at).strftime("%d.%m.%Y %H:%M")
    status_label = STATUS_LABELS[language].get(booking.status, booking.status.value)

    return (
        f"🏢 <b>{salon_name}</b>\n"
        f"💈 {service_name}\n"
        f"🕒 {when}\n"
        f"📌 {status_label}"
    )

def _cancel_keyboard(booking_id: int, language: str):
    builder = InlineKeyboardBuilder()
    text = "❌ Bekor qilish" if language == "uz" else "❌ Отменить"
    builder.button(
        text=text,
        callback_data=BookingCancelCallback(booking_id=booking_id).pack(),
    )
    return builder.as_markup()

@router.message(F.text.in_(["📅 Mening bronlarim", "📅 Мои записи"]))
async def show_my_bookings(message: Message) -> None:
    user = await user_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Avval ro'yxatdan o'ting.")
        return

    lang = user.language

    bookings = await booking_repo.get_user_bookings(user.id)
    if not bookings:
        text = "Sizda hali bronlar mavjud emas." if lang == "uz" else "У вас пока нет записей."
        await message.answer(text)
        return

    active = [b for b in bookings if b.status in ACTIVE_STATUSES]
    past = [b for b in bookings if b.status not in ACTIVE_STATUSES]

    salons, services = await _load_salons_and_services(bookings)

    if active:
        title = "📅 <b>Faol bronlaringiz</b>" if lang == "uz" else "📅 <b>Ваши активные записи</b>"
        await message.answer(title)
        for booking in active:
            await message.answer(
                _format_booking(booking, salons, services, lang),
                reply_markup=_cancel_keyboard(booking.id, lang),
            )

    if past:
        title = "🗂 <b>O'tgan bronlar</b>" if lang == "uz" else "🗂 <b>Прошедшие записи</b>"
        await message.answer(title)
        for booking in past:
            await message.answer(_format_booking(booking, salons, services, lang))

@router.callback_query(BookingCancelCallback.filter())
async def handle_cancel_booking(
    callback: CallbackQuery, callback_data: BookingCancelCallback
) -> None:
    user = await user_repo.get_user(callback.from_user.id)
    lang = user.language if user else "uz"

    booking = await booking_repo.get_booking(callback_data.booking_id)

    if booking is None:
        text = "Bron topilmadi." if lang == "uz" else "Запись не найдена."
        await callback.answer(text, show_alert=True)
        return

    if booking.status not in ACTIVE_STATUSES:
        text = "Bu bronni bekor qilib bo'lmaydi." if lang == "uz" else "Эту запись нельзя отменить."
        await callback.answer(text, show_alert=True)
        return

    time_left = booking.scheduled_at - now_utc()
    if time_left < timedelta(hours=CANCEL_MIN_HOURS):
        text = (
            f"Bronni bekor qilish uchun kamida {CANCEL_MIN_HOURS} soat qolgan bo'lishi kerak."
            if lang == "uz"
            else f"Отменить запись можно минимум за {CANCEL_MIN_HOURS} часа."
        )
        await callback.answer(text, show_alert=True)
        return

    await booking_repo.cancel_booking(booking.id)

    cancelled_label = "❌ <b>Bekor qilindi</b>" if lang == "uz" else "❌ <b>Отменено</b>"
    if callback.message.text or callback.message.html_text:
        base_text = callback.message.html_text or callback.message.text
        await callback.message.edit_text(f"{base_text}\n\n{cancelled_label}")

    confirm_text = "Bron bekor qilindi." if lang == "uz" else "Запись отменена."
    await callback.answer(confirm_text)