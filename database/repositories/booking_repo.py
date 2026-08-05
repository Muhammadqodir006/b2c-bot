from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from database.engine import async_session
from database.models import Booking, BookingStatus


async def create_booking(
    user_id: int,
    salon_id: int,
    master_id: int,
    service_id: int,
    scheduled_at: datetime,
) -> Booking:
    async with async_session() as session:
        booking = Booking(
            user_id=user_id,
            salon_id=salon_id,
            master_id=master_id,
            service_id=service_id,
            scheduled_at=scheduled_at,
            status=BookingStatus.pending,
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        return booking


async def get_booking(booking_id: int) -> Booking | None:
    async with async_session() as session:
        result = await session.execute(
            select(Booking)
            .options(
                selectinload(Booking.user),
                selectinload(Booking.master),
            )
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()


async def get_user_bookings(user_id: int, only_active: bool = False) -> list[Booking]:
    async with async_session() as session:
        stmt = (
            select(Booking)
            .options(selectinload(Booking.master))
            .where(Booking.user_id == user_id)
            .order_by(Booking.scheduled_at.desc())
        )
        if only_active:
            stmt = stmt.where(
                Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed])
            )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_master_bookings_for_slot(
    master_id: int,
    start_time: datetime,
    end_time: datetime,
) -> list[Booking]:
    """Master'ning berilgan vaqt oralig'idagi bandliklari — bo'sh vaqt hisoblash uchun."""
    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(
                and_(
                    Booking.master_id == master_id,
                    Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed]),
                    Booking.scheduled_at >= start_time,
                    Booking.scheduled_at < end_time,
                )
            )
        )
        return list(result.scalars().all())


async def update_booking_status(booking_id: int, status: BookingStatus) -> Booking | None:
    async with async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()

        if booking is None:
            return None

        booking.status = status
        await session.commit()
        await session.refresh(booking)
        return booking


async def cancel_booking(booking_id: int) -> Booking | None:
    return await update_booking_status(booking_id, BookingStatus.cancelled)


async def get_bookings_for_reminder(
    remind_after: datetime,
    remind_before: datetime,
) -> list[Booking]:
    """APScheduler job'lari uchun — belgilangan oraliqdagi confirmed bronlar."""
    async with async_session() as session:
        result = await session.execute(
            select(Booking)
            .options(selectinload(Booking.user))
            .where(
                and_(
                    Booking.status == BookingStatus.confirmed,
                    Booking.scheduled_at >= remind_after,
                    Booking.scheduled_at <= remind_before,
                )
            )
        )
        return list(result.scalars().all())