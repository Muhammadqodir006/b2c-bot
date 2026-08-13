from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def salons_keyboard(salons) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for salon in salons:
        builder.button(
            text=salon.name,
            callback_data=f"booking_salon:{salon.id}",
        )
    builder.button(text="❌ Bekor qilish", callback_data="booking_back")
    builder.adjust(1)
    return builder.as_markup()


def services_keyboard(services) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(
            text=f"{service.name} — {service.price} so'm",
            callback_data=f"booking_service:{service.id}",
        )
    builder.button(text="◀️ Orqaga", callback_data="booking_back")
    builder.adjust(1)
    return builder.as_markup()


def masters_keyboard(masters) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for master in masters:
        builder.button(
            text=master.full_name,
            callback_data=f"booking_master:{master.id}",
        )
    builder.button(text="🎲 Farqi yo'q", callback_data="booking_master:any")
    builder.button(text="◀️ Orqaga", callback_data="booking_back")
    builder.adjust(1)
    return builder.as_markup()


def times_keyboard(times: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for time_str in times:
        builder.button(
            text=time_str,
            callback_data=f"booking_time:{time_str}",
        )
    builder.button(text="◀️ Orqaga", callback_data="booking_back")
    builder.adjust(3)
    return builder.as_markup()


def confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="booking_confirm")
    builder.button(text="◀️ Orqaga", callback_data="booking_back")
    builder.adjust(1)
    return builder.as_markup()