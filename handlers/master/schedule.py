from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database.repositories.salon_repo import get_master_by_telegram_id
from database.repositories.booking_repo import (
    get_master_bookings_today,
    block_time_slot,
)
from services.time_service import to_local, to_utc

router = Router()


class BlockTimeStates(StatesGroup):
    waiting_for_range = State()


def _format_schedule(bookings, language: str) -> str:
    if not bookings:
        return (
            "Bugun hech kim yozilmagan 📭"
            if language == "uz"
            else "На сегодня записей нет 📭"
        )

    lines = []
    for booking in bookings:
        when = to_local(booking.scheduled_at).strftime("%H:%M")
        if booking.user is not None:
            lines.append(f"🕒 {when} — {booking.user.full_name} ({booking.user.phone})")
        else:
            lines.append(f"🕒 {when} — 🔒 Yopilgan vaqt")

    header = (
        "📅 Bugungi grafik:\n\n"
        if language == "uz"
        else "📅 Расписание на сегодня:\n\n"
    )
    return header + "\n".join(lines)


@router.message(F.text.in_(["📅 Bugungi grafik", "📅 Расписание на сегодня"]))
async def show_today_schedule(message: Message):
    master = await get_master_by_telegram_id(message.from_user.id)
    if master is None:
        return

    bookings = await get_master_bookings_today(master.id)
    text = _format_schedule(bookings, master.language)
    await message.answer(text)


@router.message(F.text.in_(["⏳ Vaqtni yopish", "⏳ Закрыть время"]))
async def ask_block_range(message: Message, state: FSMContext):
    master = await get_master_by_telegram_id(message.from_user.id)
    if master is None:
        return

    await state.set_state(BlockTimeStates.waiting_for_range)
    text = (
        "Yopmoqchi bo'lgan vaqtingizni shu formatda yozing: 13:00-14:00"
        if master.language == "uz"
        else "Введите время в формате: 13:00-14:00"
    )
    await message.answer(text)


@router.message(BlockTimeStates.waiting_for_range)
async def handle_block_range(message: Message, state: FSMContext):
    master = await get_master_by_telegram_id(message.from_user.id)
    if master is None:
        await state.clear()
        return

    lang = master.language

    try:
        start_str, end_str = message.text.strip().split("-")
        start_hour, start_min = map(int, start_str.strip().split(":"))
        end_hour, end_min = map(int, end_str.strip().split(":"))
    except (ValueError, AttributeError):
        text = (
            "Noto'g'ri format. Masalan: 13:00-14:00"
            if lang == "uz"
            else "Неверный формат. Например: 13:00-14:00"
        )
        await message.answer(text)
        return

    today = datetime.now().date()
    start_local = datetime.combine(today, datetime.min.time()).replace(
        hour=start_hour, minute=start_min
    )
    end_local = datetime.combine(today, datetime.min.time()).replace(
        hour=end_hour, minute=end_min
    )

    if end_local <= start_local:
        text = (
            "Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."
            if lang == "uz"
            else "Время окончания должно быть позже времени начала."
        )
        await message.answer(text)
        return

    current = start_local
    created_count = 0
    while current < end_local:
        await block_time_slot(
            master_id=master.id,
            salon_id=master.salon_id,
            start_time=to_utc(current),
            end_time=to_utc(current + timedelta(hours=1)),
        )
        current += timedelta(hours=1)
        created_count += 1

    await state.clear()

    text = (
        f"✅ {start_str.strip()}-{end_str.strip()} vaqt oralig'i yopildi."
        if lang == "uz"
        else f"✅ Время {start_str.strip()}-{end_str.strip()} закрыто."
    )
    await message.answer(text)
