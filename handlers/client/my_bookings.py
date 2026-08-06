from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from database.engine import async_session
from database.models import BookingStatus, Salon, Service
from database.repositories import booking_repo, user_repo

router = Router(name="client_my_bookings")

ACTIVE_STATUSES = (BookingStatus.pending, BookingStatus.confirmed)
CANCEL_MIN_HOURS = 2

STATUS_LABELS = {
    BookingStatus.pending: "⏳ Kutilmoqda",
    BookingStatus.confirmed: "✅ Tasdiqlangan",
    BookingStatus.completed: "🏁 Yakunlangan",
    BookingStatus.cancelled: "❌ Bekor qilingan",
    BookingStatus.no_show: "🚫 Kelmagan",
}


class BookingCancelCallback(CallbackData, prefix="bk_cancel"):
    booking_id: int


async def _load_salons_and_services(bookings: list) -> tuple[dict, dict]:
    """N+1 so'rovlarning oldini olish uchun salon/xizmat nomlarini bittada yuklaydi."""
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


def _format_booking(booking, salons: dict, services: dict) -> str:
    salon = salons.get(booking.salon_id)
    service = services.get(booking.service_id)

    salon_name = salon.name if salon else "—"
    service_name = service.name if service else "—"
    when = booking.scheduled_at.strftime("%d.%m.%Y %H:%M")
    status_label = STATUS_LABELS.get(booking.status, booking.status.value)

    return (
        f"🏢 <b>{salon_name}</b>\n"
        f"💈 {service_name}\n"
        f"🕒 {when}\n"
        f"📌 {status_label}"
    )


def _cancel_keyboard(booking_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Bekor qilish",
        callback_data=BookingCancelCallback(booking_id=booking_id).pack(),
    )
    return builder.as_markup()


@router.message(F.text == "📅 Mening bronlarim")
async def show_my_bookings(message: Message) -> None:
    user = await user_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Avval ro'yxatdan o'ting.")
        return

    bookings = await booking_repo.get_user_bookings(user.id)
    if not bookings:
        await message.answer("Sizda hali bronlar mavjud emas.")
        return

    active = [b for b in bookings if b.status in ACTIVE_STATUSES]
    past = [b for b in bookings if b.status not in ACTIVE_STATUSES]

    salons, services = await _load_salons_and_services(bookings)

    if active:
        await message.answer("📅 <b>Faol bronlaringiz</b>")
        for booking in active:
            await message.answer(
                _format_booking(booking, salons, services),
                reply_markup=_cancel_keyboard(booking.id),
            )

    if past:
        await message.answer("🗂 <b>O'tgan bronlar</b>")
        for booking in past:
            await message.answer(_format_booking(booking, salons, services))


@router.callback_query(BookingCancelCallback.filter())
async def handle_cancel_booking(
    callback: CallbackQuery, callback_data: BookingCancelCallback
) -> None:
    booking = await booking_repo.get_booking(callback_data.booking_id)

    if booking is None:
        await callback.answer("Bron topilmadi.", show_alert=True)
        return

    if booking.status not in ACTIVE_STATUSES:
        await callback.answer("Bu bronni bekor qilib bo'lmaydi.", show_alert=True)
        return

    time_left = booking.scheduled_at - datetime.utcnow()
    if time_left < timedelta(hours=CANCEL_MIN_HOURS):
        await callback.answer(
            f"Bronni bekor qilish uchun kamida {CANCEL_MIN_HOURS} soat qolgan bo'lishi kerak.",
            show_alert=True,
        )
        return

    await booking_repo.cancel_booking(booking.id)

    if callback.message.text or callback.message.html_text:
        base_text = callback.message.html_text or callback.message.text
        await callback.message.edit_text(f"{base_text}\n\n❌ <b>Bekor qilindi</b>")

    await callback.answer("Bron bekor qilindi.")