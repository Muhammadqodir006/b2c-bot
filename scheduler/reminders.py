import logging
from datetime import timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from database.repositories.booking_repo import get_booking
from services.time_service import now_utc, to_local, to_utc

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Starts the AsyncIO Scheduler if it is not already running."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started successfully.")


async def schedule_booking_reminders(bot: Bot, booking_id: int, scheduled_at):
    """
    Schedules reminder jobs for a booking:
    - 2 hours before the scheduled time
    - 15 minutes before the scheduled time
    """
    scheduled_at = to_utc(scheduled_at)

    # 2 soat oldin
    remind_2h = scheduled_at - timedelta(hours=2)
    if remind_2h > now_utc():
        scheduler.add_job(
            send_reminder,
            DateTrigger(run_date=remind_2h),
            args=[bot, booking_id, "2h"],
            id=f"reminder_2h_{booking_id}",
            replace_existing=True,
        )
        logger.info(f"Scheduled 2h reminder for booking {booking_id} at {remind_2h}")

    # 15 daqiqa oldin
    remind_15m = scheduled_at - timedelta(minutes=15)
    if remind_15m > now_utc():
        scheduler.add_job(
            send_reminder,
            DateTrigger(run_date=remind_15m),
            args=[bot, booking_id, "15m"],
            id=f"reminder_15m_{booking_id}",
            replace_existing=True,
        )
        logger.info(f"Scheduled 15m reminder for booking {booking_id} at {remind_15m}")


def cancel_booking_reminders(booking_id: int):
    """Cancels scheduled reminders for a specific booking."""
    for reminder_type in ["2h", "15m", "review"]:
        job_id = f"reminder_{reminder_type}_{booking_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Canceled job {job_id}")


async def send_reminder(bot: Bot, booking_id: int, reminder_type: str):
    """Sends reminder message to user via Telegram Bot."""
    booking = await get_booking(booking_id)
    if booking is None or booking.user is None:
        logger.warning(f"Booking or user not found for booking_id={booking_id}")
        return

    lang = getattr(booking.user, "language", "uz")
    when = to_local(booking.scheduled_at).strftime("%H:%M")

    if reminder_type == "2h":
        text = (
            f"⏰ Eslatma: soat {when} da broningiz bor"
            if lang == "uz"
            else f"⏰ Напоминание: у вас запись в {when}"
        )
    elif reminder_type == "15m":
        text = (
            f"⏰ 15 daqiqadan so'ng broningiz boshlanadi!"
            if lang == "uz"
            else f"⏰ Через 15 минут начинается ваша запись!"
        )
    elif reminder_type == "review":
        text = (
            f"🌟 Xizmatimizdan foydalanganingiz uchun rahmat! Iltimos, sharh qoldiring."
            if lang == "uz"
            else f"🌟 Спасибо, что воспользовались нашей услугой! Пожалуйста, оставьте отзыв."
        )
    else:
        text = (
            f"⏰ Eslatma: soat {when} da broningiz bor"
            if lang == "uz"
            else f"⏰ Напоминание: у вас запись в {when}"
        )

    try:
        await bot.send_message(chat_id=booking.user.telegram_id, text=text)
        logger.info(f"Sent '{reminder_type}' reminder to user {booking.user.telegram_id} for booking {booking_id}")
    except Exception as e:
        logger.error(f"Error sending message to user {booking.user.telegram_id}: {e}")