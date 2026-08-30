from aiogram import Bot, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings
from database.models import BookingStatus, Booking
from database.repositories.booking_repo import get_booking, update_booking_status, async_session
from database.repositories.user_repo import adjust_trust_score
from services.time_service import to_local
from handlers.client.review import send_review_request
from services.points_service import add_points, check_and_award_badges
from sqlalchemy import select, func

client_bot = Bot(token=settings.client_bot_token)


router = Router()


class BookingArrivedCallback(CallbackData, prefix="booking_arrived"):
    booking_id: int


class BookingNoShowCallback(CallbackData, prefix="booking_noshow"):
    booking_id: int


def _notification_keyboard(booking_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Mijoz keldi",
        callback_data=BookingArrivedCallback(booking_id=booking_id).pack(),
    )
    builder.button(
        text="❌ Kelmadi",
        callback_data=BookingNoShowCallback(booking_id=booking_id).pack(),
    )

    builder.adjust(2)
    return builder.as_markup()


async def send_new_booking_notification(
    bot: Bot,
    booking_id: int,
) -> bool:
    booking = await get_booking(booking_id)

    if booking is None or booking.master is None or booking.master.telegram_id is None:
        return False

    master = booking.master
    language = master.language

    when = to_local(booking.scheduled_at).strftime("%d.%m.%Y %H:%M")
    client_name = booking.user.full_name if booking.user else "—"
    client_phone = booking.user.phone if booking.user else "—"

    if language == "ru":
        text = (
            "⚡️ НОВАЯ ЗАПИСЬ!\n"
            f"👤 Клиент: {client_name} ({client_phone})\n"
            f"🕒 Время: {when}"
        )
    else:
        text = (
            f"⚡️ YANGI BRON!\n👤 Mijoz: {client_name} ({client_phone})\n🕒 Vaqt: {when}"
        )

    await bot.send_message(
        chat_id=master.telegram_id,
        text=text,
        reply_markup=_notification_keyboard(booking_id),
    )

    return True


@router.callback_query(BookingArrivedCallback.filter())
async def handle_arrived(
    callback: CallbackQuery, callback_data: BookingArrivedCallback, bot: Bot
):
    booking = await update_booking_status(
        callback_data.booking_id,
        BookingStatus.completed,
    )
    await update_booking_status(callback_data.booking_id, BookingStatus.completed)
    booking = await get_booking(callback_data.booking_id)

    if booking is None:
        await callback.answer("Bron topilmadi.", show_alert=True)
        return
    
    if booking.user is not None:
        await adjust_trust_score(booking.user.telegram_id, +5)
        await add_points(booking.user.id, 10, "completed_booking")

        async with async_session() as session:
            result = await session.execute(
                select(func.count(Booking.id)).where(
                    Booking.user_id == booking.user.id,
                    Booking.status == BookingStatus.completed,
                )
            )
            total_completed = result.scalar()

        earned_badges = await check_and_award_badges(booking.user.id, total_completed)
        if earned_badges:
            badge_text = ", ".join(earned_badges)
            await client_bot.send_message(
                chat_id=booking.user.telegram_id,
                text=f"🎖 Tabriklaymiz! Yangi belgi oldingiz: {badge_text}"
            )

    language = booking.master.language if booking.master else "uz"

    if language == "ru":
        text = f"{callback.message.text}\n\n✅ Клиент пришёл"
    else:
        text = f"{callback.message.text}\n\n✅ Mijoz keldi"

    await callback.message.edit_text(text)
    await callback.answer()

    await send_review_request(client_bot, callback_data.booking_id)


@router.callback_query(BookingNoShowCallback.filter())
async def handle_no_show(
    callback: CallbackQuery,
    callback_data: BookingNoShowCallback,
):
    booking = await update_booking_status(
        callback_data.booking_id,
        BookingStatus.no_show,
    )
    await update_booking_status(callback_data.booking_id, BookingStatus.no_show)
    booking = await get_booking(callback_data.booking_id)

    if booking is None:
        await callback.answer("Bron topilmadi.", show_alert=True)
        return
    
    if booking.user is not None:
        await adjust_trust_score(booking.user.telegram_id, -10)
        client_lang = booking.user.language
        when = to_local(booking.scheduled_at).strftime("%d.%m.%Y %H:%M")
        if client_lang == "ru":
            client_text = f"❌ Вы не пришли на запись {when}. Это может повлиять на ваш рейтинг доверия."
        else:
            client_text = f"❌ Siz {when} dagi bronga kelmadingiz. Bu ishonchlilik ballingizga ta'sir qilishi mumkin."
        await client_bot.send_message(chat_id=booking.user.telegram_id, text=client_text)

    language = booking.master.language if booking.master else "uz"

    if language == "ru":
        text = f"{callback.message.text}\n\n❌ Клиент не пришёл"
    else:
        text = f"{callback.message.text}\n\n❌ Kelmadi"

    await callback.message.edit_text(text)
    await callback.answer()

async def send_booking_cancelled_notification(bot: Bot, booking_id: int) -> bool:
    booking = await get_booking(booking_id)

    if (
        booking is None
        or booking.master is None
        or booking.master.telegram_id is None
    ):
        return False

    master = booking.master
    language = master.language

    when = to_local(booking.scheduled_at).strftime("%d.%m.%Y %H:%M")
    client_name = booking.user.full_name if booking.user else "—"

    if language == "ru":
        text = (
            "❌ ЗАПИСЬ ОТМЕНЕНА\n"
            f"👤 Клиент: {client_name}\n"
            f"🕒 Время: {when}"
        )
    else:
        text = (
            "❌ BRON BEKOR QILINDI\n"
            f"👤 Mijoz: {client_name}\n"
            f"🕒 Vaqt: {when}"
        )

    await bot.send_message(chat_id=master.telegram_id, text=text)
    return True
