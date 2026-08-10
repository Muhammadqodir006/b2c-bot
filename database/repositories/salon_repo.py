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
    
async def get_master_by_phone(phone: str) -> Master | None:
    async with async_session() as session:
        result = await session.execute(
            select(Master).where(Master.phone == phone)
        )
        return result.scalar_one_or_none()
    
async def link_master_telegram(master_id: int, telegram_id: int) -> Master | None:
    async with async_session() as session:
        result = await session.execute(
            select(Master).where(Master.id == master_id)
        )
        master = result.scalar_one_or_none()
        if master is None:
            return None
        master.telegram_id = telegram_id
        await session.commit()
        await session.refresh(master)
        return master
    
async def update_master_language(master_id: int, language: str) -> Master | None:
    async with async_session() as session:
        result = await session.execute(
            select(Master).where(Master.id == master_id)
        )
        master = result.scalar_one_or_none()
        if master is None:
            return None
        master.language = language
        await session.commit()
        await session.refresh(master)
        return master

async def create_master(salon_id: int, full_name: str, phone: str) -> Master:
    async with async_session() as session:
        master = Master(salon_id=salon_id, full_name=full_name, phone=phone)
        session.add(master)
        await session.commit()
        await session.refresh(master)
        return master


async def get_salons_by_category(category_id: int) -> list[Salon]:
    async with async_session() as session:
        result = await session.execute(
            select(Salon)
            .join(Service, Service.salon_id == Salon.id)
            .where(Service.category_id == category_id)
            .distinct()
        )
        return list(result.scalars().all())