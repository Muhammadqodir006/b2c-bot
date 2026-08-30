from database.engine import async_session
from database.models import UserPoints, PointsLog, Badge, UserBadge, User
from sqlalchemy import select

POINTS_FOR_COMPLETED_BOOKING = 10
POINTS_FOR_REFERRAL = 20


async def add_points(user_id: int, points: int, action_type: str) -> UserPoints:
    async with async_session() as session:
        result = await session.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        user_points = result.scalar_one_or_none()

        if user_points is None:
            user_points = UserPoints(user_id=user_id, total_points=0)
            session.add(user_points)
            await session.flush()

        user_points.total_points += points

        log = PointsLog(user_id=user_id, action_type=action_type, points=points)
        session.add(log)

        await session.commit()
        await session.refresh(user_points)
        return user_points


async def get_user_points(user_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        user_points = result.scalar_one_or_none()
        return user_points.total_points if user_points else 0


async def check_and_award_badges(user_id: int, total_completed_bookings: int) -> list[str]:
    """Oddiy qoida asosida badge beradi. Yangi olingan badge nomlarini qaytaradi."""
    earned = []

    milestones = {
        1: "first_booking",
        5: "loyal_client",
        10: "vip_client",
    }

    badge_code = milestones.get(total_completed_bookings)
    if badge_code is None:
        return earned

    async with async_session() as session:
        result = await session.execute(select(Badge).where(Badge.code == badge_code))
        badge = result.scalar_one_or_none()
        if badge is None:
            return earned

        result = await session.execute(
            select(UserBadge).where(
                UserBadge.user_id == user_id, UserBadge.badge_id == badge.id
            )
        )
        already_has = result.scalar_one_or_none()
        if already_has is not None:
            return earned

        user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
        session.add(user_badge)
        await session.commit()
        earned.append(badge.name)

    return earned