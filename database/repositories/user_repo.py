from sqlalchemy import select
from database.engine import async_session
from database.models import User


async def get_or_create_user(telegram_id: int, full_name: str) -> User:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(telegram_id=telegram_id, full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


async def update_phone(telegram_id: int, phone: str) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            return None

        user.phone = phone
        await session.commit()
        await session.refresh(user)
        return user


async def get_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def update_language(telegram_id: int, language: str) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            return None
        user.language = language
        await session.commit()
        await session.refresh(user)
        return user

async def adjust_trust_score(telegram_id: int, delta: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            return None

        new_score = user.trust_score + delta
        user.trust_score = max(0, min(100, new_score))  # 0-100 oralig'ida ushlab turadi

        await session.commit()
        await session.refresh(user)
        return user