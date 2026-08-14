from datetime import timedelta
from aiogram import Bot
from config import settings
from handlers.master.notifications import send_new_booking_notification
from scheduler.reminders import schedule_booking_reminders
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.booking_states import BookingStates

from keyboards.client.booking_kb import (
    salons_keyboard,
    services_keyboard,
    masters_keyboard,
    times_keyboard,
    confirmation_keyboard,
)

from database.repositories import salon_repo, booking_repo
from database.repositories.user_repo import get_or_create_user
from services.time_service import now_utc, to_utc, to_local
from services.booking_service import is_slot_available

master_bot = Bot(token=settings.master_bot_token)


router = Router()


# ============================================================
# 1. BRONNI BOSHLASH
# ============================================================

@router.callback_query(F.data == "booking_start")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    salons = await salon_repo.get_all_salons()

    if not salons:
        await callback.message.edit_text(
            "Hozircha salonlar mavjud emas."
        )
        await callback.answer()
        return

    await state.clear()
    await state.set_state(BookingStates.choosing_salon)

    await callback.message.edit_text(
        "🏢 Salonni tanlang:",
        reply_markup=salons_keyboard(salons),
    )

    await callback.answer()


# ============================================================
# 2. SALON TANLASH
# ============================================================

@router.callback_query(
    BookingStates.choosing_salon,
    F.data.startswith("booking_salon:")
)
async def choose_salon(callback: CallbackQuery, state: FSMContext):
    salon_id = int(callback.data.split(":")[1])

    salon = await salon_repo.get_salon(salon_id)

    if salon is None:
        await callback.answer(
            "Salon topilmadi.",
            show_alert=True,
        )
        return

    services = await salon_repo.get_services_by_salon(salon_id)

    if not services:
        await callback.answer(
            "Bu salonda xizmatlar mavjud emas.",
            show_alert=True,
        )
        return

    await state.update_data(
        salon_id=salon_id,
        salon_name=salon.name,
    )

    await state.set_state(BookingStates.choosing_service)

    await callback.message.edit_text(
        f"🏢 {salon.name}\n\n"
        "💈 Xizmatni tanlang:",
        reply_markup=services_keyboard(services),
    )

    await callback.answer()


# ============================================================
# 3. XIZMAT TANLASH
# ============================================================

@router.callback_query(
    BookingStates.choosing_service,
    F.data.startswith("booking_service:")
)
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])

    data = await state.get_data()
    salon_id = data["salon_id"]

    services = await salon_repo.get_services_by_salon(salon_id)

    service = next(
        (service for service in services if service.id == service_id),
        None,
    )

    if service is None:
        await callback.answer(
            "Xizmat topilmadi.",
            show_alert=True,
        )
        return

    masters = await salon_repo.get_masters_by_salon(salon_id)

    if not masters:
        await callback.answer(
            "Bu salonda ustalar mavjud emas.",
            show_alert=True,
        )
        return

    await state.update_data(
        service_id=service.id,
        service_name=service.name,
        service_price=service.price,
        duration_minutes=service.duration_minutes,
    )

    await state.set_state(BookingStates.choosing_master)

    await callback.message.edit_text(
        f"💈 Xizmat: {service.name}\n"
        f"💰 Narx: {service.price}\n"
        f"⏱ Davomiyligi: {service.duration_minutes} daqiqa\n\n"
        "👨‍💼 Ustani tanlang:",
        reply_markup=masters_keyboard(masters),
    )

    await callback.answer()


# ============================================================
# 4. USTA TANLASH
# ============================================================

@router.callback_query(
    BookingStates.choosing_master,
    F.data.startswith("booking_master:")
)
async def choose_master(callback: CallbackQuery, state: FSMContext):
    master_value = callback.data.split(":")[1]

    data = await state.get_data()
    salon_id = data["salon_id"]

    masters = await salon_repo.get_masters_by_salon(salon_id)

    if not masters:
        await callback.answer(
            "Ustalar topilmadi.",
            show_alert=True,
        )
        return

    if master_value == "any":
        await state.update_data(
            master_id=None,
            master_name="Farqi yo'q",
        )
    else:
        master_id = int(master_value)

        master = next(
            (master for master in masters if master.id == master_id),
            None,
        )

        if master is None:
            await callback.answer(
                "Usta topilmadi.",
                show_alert=True,
            )
            return

        await state.update_data(
            master_id=master.id,
            master_name=master.full_name,
        )

    await state.set_state(BookingStates.choosing_time)

    await show_available_times(
        callback,
        state,
        masters,
    )

    await callback.answer()


# ============================================================
# BO'SH VAQTLARNI TOPISH
# ============================================================

async def show_available_times(
    callback: CallbackQuery,
    state: FSMContext,
    masters,
):
    data = await state.get_data()

    selected_master_id = data.get("master_id")
    duration = data["duration_minutes"]

    # Hozirgi vaqtni Toshkent vaqtida hisoblaymiz — ish vaqti ham shu bo'yicha
    now_local = to_local(now_utc())

    work_start_local = now_local.replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0,
    )

    work_end_local = now_local.replace(
        hour=18,
        minute=0,
        second=0,
        microsecond=0,
    )

    available_times = []

    current_local = work_start_local

    while current_local + timedelta(minutes=duration) <= work_end_local:

        # O'tib ketgan vaqtlarni ko'rsatmaymiz (Toshkent vaqti bo'yicha solishtirish)
        if current_local <= now_local:
            current_local += timedelta(minutes=30)
            continue

        # Bazada solishtirish uchun UTC'ga aylantiramiz
        current_utc = to_utc(current_local)
        slot_end_utc = current_utc + timedelta(minutes=duration)

        # Agar foydalanuvchi aniq usta tanlagan bo'lsa
        if selected_master_id is not None:

            bookings = await booking_repo.get_master_bookings_for_slot(
                selected_master_id,
                current_utc,
                slot_end_utc,
            )

            if not bookings:
                available_times.append(
                    current_local.strftime("%H:%M")
                )

        # "Farqi yo'q" bo'lsa
        else:

            for master in masters:
                bookings = (
                    await booking_repo.get_master_bookings_for_slot(
                        master.id,
                        current_utc,
                        slot_end_utc,
                    )
                )

                if not bookings:
                    available_times.append(
                        current_local.strftime("%H:%M")
                    )
                    break

        current_local += timedelta(minutes=30)

    if not available_times:
        await callback.message.edit_text(
            "😔 Bugun bo'sh vaqt topilmadi.",
            reply_markup=times_keyboard([]),
        )
        return

    await callback.message.edit_text(
        "🕐 Bo'sh vaqtni tanlang:",
        reply_markup=times_keyboard(available_times),
    )


# ============================================================
# 5. VAQT TANLASH
# ============================================================

@router.callback_query(
    BookingStates.choosing_time,
    F.data.startswith("booking_time:")
)
async def choose_time(callback: CallbackQuery, state: FSMContext):
    selected_time = callback.data.split(":", 1)[1]

    data = await state.get_data()

    salon_id = data["salon_id"]
    duration = data["duration_minutes"]
    selected_master_id = data.get("master_id")

    hour, minute = map(int, selected_time.split(":"))

    # Tanlangan vaqt — Toshkent (local) vaqti
    now_local = to_local(now_utc())
    scheduled_at_local = now_local.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    # Bazaga yozish/solishtirish uchun UTC'ga aylantiramiz
    scheduled_at_utc = to_utc(scheduled_at_local)
    slot_end_utc = scheduled_at_utc + timedelta(minutes=duration)

    masters = await salon_repo.get_masters_by_salon(salon_id)

    if not masters:
        await callback.answer(
            "Ustalar topilmadi.",
            show_alert=True,
        )
        return

    # Agar "Farqi yo'q" tanlangan bo'lsa,
    # shu vaqt uchun bo'sh ustani topamiz.
    if selected_master_id is None:

        selected_master = None

        for master in masters:
            bookings = (
                await booking_repo.get_master_bookings_for_slot(
                    master.id,
                    scheduled_at_utc,
                    slot_end_utc,
                )
            )

            if not bookings:
                selected_master = master
                break

        if selected_master is None:
            await callback.answer(
                "Bu vaqt hozir band bo'lib qoldi. Boshqa vaqt tanlang.",
                show_alert=True,
            )
            return

        await state.update_data(
            master_id=selected_master.id,
            master_name=selected_master.full_name,
        )

    else:

        bookings = await booking_repo.get_master_bookings_for_slot(
            selected_master_id,
            scheduled_at_utc,
            slot_end_utc,
        )

        if bookings:
            await callback.answer(
                "Bu vaqt hozir band bo'lib qoldi. Boshqa vaqt tanlang.",
                show_alert=True,
            )
            return

    await state.update_data(
        scheduled_at=scheduled_at_utc,  # UTC — bazaga shu holda yoziladi
        scheduled_time=selected_time,    # faqat ko'rsatish uchun (local matn)
    )

    await state.set_state(BookingStates.confirming)

    data = await state.get_data()

    await callback.message.edit_text(
        "📋 <b>Bron ma'lumotlari</b>\n\n"
        f"🏢 Salon: {data['salon_name']}\n"
        f"💈 Xizmat: {data['service_name']}\n"
        f"👨‍💼 Usta: {data['master_name']}\n"
        f"🕐 Vaqt: {data['scheduled_time']}\n"
        f"💰 Narx: {data['service_price']}\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=confirmation_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# 6. TASDIQLASH
# ============================================================

@router.callback_query(
    BookingStates.confirming,
    F.data == "booking_confirm"
)
async def confirm_booking(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()

    # Oxirgi tekshiruv — tasdiqlashgacha vaqt band bo'lib qolmaganmi
    available = await is_slot_available(
        data["master_id"],
        data["scheduled_at"],
        data["duration_minutes"],
    )

    if not available:
        await callback.message.edit_text(
            "😔 Kechirasiz, bu vaqt band bo'lib qoldi. Boshqa vaqt tanlang."
        )
        await state.clear()
        await callback.answer()
        return

    # Telegram foydalanuvchisini DBdan topamiz
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
    )

    if user is None:
        await callback.answer(
            "Foydalanuvchi topilmadi.",
            show_alert=True,
        )
        return

    booking = await booking_repo.create_booking(
        user_id=user.id,
        salon_id=data["salon_id"],
        master_id=data["master_id"],
        service_id=data["service_id"],
        scheduled_at=data["scheduled_at"],
    )
    
    # --- INTEGRATSIYA: usta xabar olsin va eslatma rejalashtirilsin ---
    await send_new_booking_notification(master_bot, booking.id)
    await schedule_booking_reminders(bot, booking.id, booking.scheduled_at)
    # ------------------------------------------------------------------

    await callback.message.edit_text(
        "✅ <b>Bron muvaffaqiyatli yaratildi!</b>\n\n"
        f"🏢 Salon: {data['salon_name']}\n"
        f"💈 Xizmat: {data['service_name']}\n"
        f"👨‍💼 Usta: {data['master_name']}\n"
        f"🕐 Vaqt: {data['scheduled_time']}\n\n"
        f"🆔 Bron raqami: #{booking.id}",
        parse_mode="HTML",
    )

    await state.clear()
    await callback.answer()


# ============================================================
# 7. ORQAGA
# ============================================================

@router.callback_query(
    BookingStates.choosing_service,
    F.data == "booking_back"
)
async def back_to_salon(
    callback: CallbackQuery,
    state: FSMContext,
):
    salons = await salon_repo.get_all_salons()

    await state.set_state(BookingStates.choosing_salon)

    await callback.message.edit_text(
        "🏢 Salonni tanlang:",
        reply_markup=salons_keyboard(salons),
    )

    await callback.answer()


@router.callback_query(
    BookingStates.choosing_master,
    F.data == "booking_back"
)
async def back_to_service(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()

    services = await salon_repo.get_services_by_salon(
        data["salon_id"]
    )

    await state.set_state(BookingStates.choosing_service)

    await callback.message.edit_text(
        "💈 Xizmatni tanlang:",
        reply_markup=services_keyboard(services),
    )

    await callback.answer()


@router.callback_query(
    BookingStates.choosing_time,
    F.data == "booking_back"
)
async def back_to_master(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()

    masters = await salon_repo.get_masters_by_salon(
        data["salon_id"]
    )

    await state.set_state(BookingStates.choosing_master)

    await callback.message.edit_text(
        "👨‍💼 Ustani tanlang:",
        reply_markup=masters_keyboard(masters),
    )

    await callback.answer()


@router.callback_query(
    BookingStates.confirming,
    F.data == "booking_back"
)
async def back_to_time(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()

    masters = await salon_repo.get_masters_by_salon(
        data["salon_id"]
    )

    await state.set_state(BookingStates.choosing_time)

    await show_available_times(
        callback,
        state,
        masters,
    )

    await callback.answer()


# ============================================================
# 8. UNIVERSAL BACK
# ============================================================

@router.callback_query(
    BookingStates.choosing_salon,
    F.data == "booking_back"
)
async def back_from_salon(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    await callback.message.edit_text(
        "❌ Bron qilish bekor qilindi."
    )

    await callback.answer()