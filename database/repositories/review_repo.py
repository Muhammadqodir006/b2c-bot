from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.engine import async_session
from database.models import Review


async def create_review(booking_id: int, rating: int, comment: str | None = None) -> Review | None:
    async with async_session() as session:
        review = Review(booking_id=booking_id, rating=rating, comment=comment)
        session.add(review)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return await get_review_by_booking(booking_id)

        await session.refresh(review)
        return review


async def get_review_by_booking(booking_id: int) -> Review | None:
    async with async_session() as session:
        result = await session.execute(
            select(Review).where(Review.booking_id == booking_id)
        )
        return result.scalar_one_or_none()