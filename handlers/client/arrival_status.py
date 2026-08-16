from aiogram import Router, Bot
from aiogram.types import CallbackQuery

from config import settings
from database.repositories.booking_repo import get_booking
from keyboards.client.arrival_kb import ArrivalStatusCallback

router = Router()

master_bot = Bot(token=settings.master_bot_token)


@router.callback_query(ArrivalStatusCallback.filter())
async def handle_arrival_status(callback: CallbackQuery, callback_data: ArrivalStatusCallback):
    booking = await get_booking(callback_data.booking_id)

    if booking is None or booking.master is None or booking.master.telegram_id is None:
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
        return

    client_name = booking.user.full_name if booking.user else "—"
    master_lang = booking.master.language

    if callback_data.status == "coming":
        client_text = "✅ Kelyapman, deb belgiladingiz."
        if master_lang == "ru":
            master_text = f"✅ Клиент {client_name} уже идёт к вам."
        else:
            master_text = f"✅ Mijoz {client_name} kelyapti."
    else:
        client_text = "⏰ Kechikaman, deb belgiladingiz."
        if master_lang == "ru":
            master_text = f"⏰ Клиент {client_name} опаздывает."
        else:
            master_text = f"⏰ Mijoz {client_name} kechikmoqda."

    await master_bot.send_message(chat_id=booking.master.telegram_id, text=master_text)

    await callback.message.edit_text(callback.message.text + f"\n\n{client_text}")
    await callback.answer()