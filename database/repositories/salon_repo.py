from sqlalchemy import select
from database.engine import async_session
from database.models import Salon, Service, Master


async def get_all_salons() -> list[Salon]:
    async with async_session() as session:
        result = await session.execute(select(Salon))
        return list(result.scalars().all())


async def get_salon(salon_id: int) -> Salon | None:
    async with async_session() as session:
        result = await session.execute(
            select(Salon).where(Salon.id == salon_id)
        )
        return result.scalar_one_or_none()


async def get_services_by_salon(salon_id: int) -> list[Service]:
    async with async_session() as session:
        result = await session.execute(
            select(Service).where(Service.salon_id == salon_id)
        )
        return list(result.scalars().all())


async def get_masters_by_salon(salon_id: int) -> list[Master]:
    async with async_session() as session:
        result = await session.execute(
            select(Master).where(Master.salon_id == salon_id)
        )
        return list(result.scalars().all())


async def get_master_by_telegram_id(telegram_id: int) -> Master | None:
    async with async_session() as session:
        result = await session.execute(
            select(Master).where(Master.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()