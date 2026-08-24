from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ArrivalStatusCallback(CallbackData, prefix="arrival"):
    booking_id: int
    status: str  # "coming" yoki "late"


def arrival_keyboard(booking_id: int, language: str = "uz"):
    builder = InlineKeyboardBuilder()
    coming_text = "✅ Kelyapman" if language == "uz" else "✅ Уже иду"
    late_text = "⏰ Kechikaman" if language == "uz" else "⏰ Опаздываю"

    builder.button(
        text=coming_text,
        callback_data=ArrivalStatusCallback(booking_id=booking_id, status="coming").pack(),
    )
    builder.button(
        text=late_text,
        callback_data=ArrivalStatusCallback(booking_id=booking_id, status="late").pack(),
    )
    builder.adjust(2)
    return builder.as_markup()