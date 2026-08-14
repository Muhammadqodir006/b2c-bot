from datetime import datetime, timedelta

from database.repositories.booking_repo import get_master_bookings_for_slot


WORK_START_HOUR = 9
WORK_END_HOUR = 18
SLOT_DURATION_MINUTES = 60


async def get_available_slots(
    master_id: int,
    date: datetime,
    work_start_hour: int = WORK_START_HOUR,
    work_end_hour: int = WORK_END_HOUR,
    slot_duration_minutes: int = SLOT_DURATION_MINUTES,
) -> list[datetime]:
    day_start = date.replace(
        hour=work_start_hour,
        minute=0,
        second=0,
        microsecond=0,
    )
    day_end = date.replace(
        hour=work_end_hour,
        minute=0,
        second=0,
        microsecond=0,
    )

    available_slots = []
    current = day_start

    while current + timedelta(minutes=slot_duration_minutes) <= day_end:
        slot_end = current + timedelta(minutes=slot_duration_minutes)

        bookings = await get_master_bookings_for_slot(
            master_id=master_id,
            start_time=current,
            end_time=slot_end,
        )

        if not bookings:
            available_slots.append(current)

        current = slot_end

    return available_slots


async def is_slot_available(
    master_id: int, start_time: datetime, duration_minutes: int
) -> bool:
    """Berilgan vaqt band emasligini tekshiradi — tasdiqlashdan oldin oxirgi tekshiruv uchun."""
    end_time = start_time + timedelta(minutes=duration_minutes)
    bookings = await get_master_bookings_for_slot(master_id, start_time, end_time)
    return len(bookings) == 0
