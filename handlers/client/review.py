from aiogram import Bot, Router
from aiogram.filters import StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.repositories import booking_repo, review_repo, user_repo

router = Router(name="client_review")

STAR = "⭐️"


class ReviewStates(StatesGroup):
    waiting_comment = State()


class ReviewRatingCallback(CallbackData, prefix="review_rate"):
    booking_id: int
    rating: int


class ReviewSkipCallback(CallbackData, prefix="review_skip"):
    booking_id: int
    rating: int


def _rating_keyboard(booking_id: int):
    builder = InlineKeyboardBuilder()
    for rating in range(1, 6):
        builder.button(
            text=STAR * rating,
            callback_data=ReviewRatingCallback(
                booking_id=booking_id, rating=rating
            ).pack(),
        )
    builder.adjust(1)
    return builder.as_markup()


def _comment_keyboard(booking_id: int, rating: int, language: str):
    builder = InlineKeyboardBuilder()
    text = "➡️ O'tkazib yuborish" if language == "uz" else "➡️ Пропустить"
    builder.button(
        text=text,
        callback_data=ReviewSkipCallback(booking_id=booking_id, rating=rating).pack(),
    )
    return builder.as_markup()


async def send_review_request(bot: Bot, booking_id: int) -> bool:
    booking = await booking_repo.get_booking(booking_id)
    if booking is None or booking.user is None:
        return False

    lang = booking.user.language
    text = (
        "Xizmatimizdan qanday foydalandingiz? Iltimos, baholang:"
        if lang == "uz"
        else "Как вам наш сервис? Пожалуйста, оцените:"
    )

    await bot.send_message(
        chat_id=booking.user.telegram_id,
        text=text,
        reply_markup=_rating_keyboard(booking_id),
    )
    return True


@router.callback_query(ReviewRatingCallback.filter())
async def handle_rating_selected(
    callback: CallbackQuery, callback_data: ReviewRatingCallback, state: FSMContext
) -> None:
    user = await user_repo.get_user(callback.from_user.id)
    lang = user.language if user else "uz"

    await state.set_state(ReviewStates.waiting_comment)
    await state.update_data(
        booking_id=callback_data.booking_id, rating=callback_data.rating
    )

    text = (
        f"Bahoyingiz: {STAR * callback_data.rating}\n\nXohlasangiz, sharh matnini yozib qoldiring (yoki o'tkazib yuboring)."
        if lang == "uz"
        else f"Ваша оценка: {STAR * callback_data.rating}\n\nПри желании напишите комментарий (или пропустите)."
    )

    await callback.message.edit_text(
        text,
        reply_markup=_comment_keyboard(
            callback_data.booking_id, callback_data.rating, lang
        ),
    )
    await callback.answer()


@router.message(StateFilter(ReviewStates.waiting_comment))
async def handle_review_comment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    booking_id = data.get("booking_id")
    rating = data.get("rating")
    await state.clear()

    if booking_id is None or rating is None:
        return

    user = await user_repo.get_user(message.from_user.id)
    lang = user.language if user else "uz"

    await review_repo.create_review(
        booking_id=booking_id, rating=rating, comment=message.text
    )
    text = (
        "Rahmat! Sharhingiz uchun tashakkur 🙏"
        if lang == "uz"
        else "Спасибо за отзыв! 🙏"
    )
    await message.answer(text)


@router.callback_query(ReviewSkipCallback.filter())
async def handle_review_skip(
    callback: CallbackQuery, callback_data: ReviewSkipCallback, state: FSMContext
) -> None:
    await state.clear()

    user = await user_repo.get_user(callback.from_user.id)
    lang = user.language if user else "uz"

    await review_repo.create_review(
        booking_id=callback_data.booking_id,
        rating=callback_data.rating,
        comment=None,
    )

    text = (
        f"Bahoyingiz: {STAR * callback_data.rating}\n\nRahmat! 🙏"
        if lang == "uz"
        else f"Ваша оценка: {STAR * callback_data.rating}\n\nСпасибо! 🙏"
    )
    await callback.message.edit_text(text)
    await callback.answer()
