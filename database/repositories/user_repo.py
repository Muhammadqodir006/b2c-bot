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