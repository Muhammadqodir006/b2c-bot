import logging
from datetime import timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from keyboards.client.arrival_kb import arrival_keyboard
from database.repositories.booking_repo import get_booking
from services.time_service import now_utc, to_local

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


from apscheduler.triggers.interval import IntervalTrigger

def start_scheduler():
    """Starts the AsyncIO Scheduler if it is not already running."""
    if not scheduler.running:
        scheduler.add_job(
            sync_redis_leaderboard,
            IntervalTrigger(hours=1),
            id="sync_redis_leaderboard",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduler started successfully.")

async def sync_redis_leaderboard():
    """Syncs PostgreSQL UserPoints to Redis leaderboard."""
    from database.repositories.user_repo import get_all_user_points
    from services.rating_service import rating_service

    try:
        pg_points = await get_all_user_points()
        pg_dict = {str(row.user_id): row.total_points for row in pg_points}

        # Fetch current redis leaderboard
        redis_data = await rating_service.redis_client.zrange(
            rating_service.leaderboard_key, 0, -1, withscores=True
        )
        redis_dict = {str(k): v for k, v in redis_data}

        # Update or add from postgres to redis
        to_add = {k: v for k, v in pg_dict.items() if redis_dict.get(k) != v}
        if to_add:
            await rating_service.redis_client.zadd(rating_service.leaderboard_key, to_add)

        # Remove keys in redis that are not in postgres
        to_remove = [k for k in redis_dict if k not in pg_dict]
        if to_remove:
            await rating_service.redis_client.zrem(rating_service.leaderboard_key, *to_remove)

        logger.info(f"Leaderboard synced. Updated/Added: {len(to_add)}, Removed: {len(to_remove)}")
    except Exception as e:
        logger.error(f"Error syncing leaderboard: {e}")


async def schedule_booking_reminders(bot: Bot, booking_id: int, scheduled_at):
    """
    Bron uchun eslatma job'larini rejalashtiradi:
    - 2 soat oldin
    - 15 daqiqa oldin

    scheduled_at — bazadagi qiymat, ALLAQACHON UTC. Qayta konvertatsiya qilinmaydi.
    """
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
    """Bekor qilingan bron uchun rejalashtirilgan eslatmalarni bekor qiladi."""
    for reminder_type in ["2h", "15m", "review"]:
        job_id = f"reminder_{reminder_type}_{booking_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Canceled job {job_id}")

async def send_reminder(bot: Bot, booking_id: int, reminder_type: str):
    booking = await get_booking(booking_id)
    if booking is None or booking.user is None:
        logger.warning(f"Booking or user not found for booking_id={booking_id}")
        return

    lang = getattr(booking.user, "language", "uz")
    when = to_local(booking.scheduled_at).strftime("%H:%M")
    reply_markup = None

    if reminder_type == "2h":
        text = (
            f"⏰ Eslatma: soat {when} da broningiz bor"
            if lang == "uz"
            else f"⏰ Напоминание: у вас запись в {when}"
        )
    elif reminder_type == "15m":
        text = (
            "⏰ 15 daqiqadan so'ng broningiz boshlanadi!"
            if lang == "uz"
            else "⏰ Через 15 минут начинается ваша запись!"
        )
        reply_markup = arrival_keyboard(booking_id, lang)
    elif reminder_type == "review":
        text = (
            "🌟 Xizmatimizdan foydalanganingiz uchun rahmat! Iltimos, sharh qoldiring."
            if lang == "uz"
            else "🌟 Спасибо, что воспользовались нашей услугой! Пожалуйста, оставьте отзыв."
        )
    else:
        text = (
            f"⏰ Eslatma: soat {when} da broningiz bor"
            if lang == "uz"
            else f"⏰ Напоминание: у вас запись в {when}"
        )

    try:
        await bot.send_message(chat_id=booking.user.telegram_id, text=text, reply_markup=reply_markup)
        logger.info(f"Sent '{reminder_type}' reminder to user {booking.user.telegram_id} for booking {booking_id}")
    except Exception as e:
        logger.error(f"Error sending message to user {booking.user.telegram_id}: {e}")
