from sqlalchemy import select
from database.engine import async_session
from database.models import Salon, Service, Master, Category


async def get_all_salons() -> list[Salon]:
    async with async_session() as session:
        result = await session.execute(select(Salon))
        return list(result.scalars().all())


async def get_salon(salon_id: int) -> Salon | None:
    async with async_session() as session:
        result = await session.execute(select(Salon).where(Salon.id == salon_id))
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
        result = await session.execute(select(Master).where(Master.phone == phone))
        return result.scalar_one_or_none()


async def link_master_telegram(master_id: int, telegram_id: int) -> Master | None:
    async with async_session() as session:
        result = await session.execute(select(Master).where(Master.id == master_id))
        master = result.scalar_one_or_none()
        if master is None:
            return None
        master.telegram_id = telegram_id
        await session.commit()
        await session.refresh(master)
        return master


async def update_master_language(master_id: int, language: str) -> Master | None:
    async with async_session() as session:
        result = await session.execute(select(Master).where(Master.id == master_id))
        master = result.scalar_one_or_none()
        if master is None:
            return None
        master.language = language
        await session.commit()
        await session.refresh(master)
        return master


async def create_master(salon_id: int | None, full_name: str, phone: str) -> Master:
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


async def create_salon(
    name: str,
    address: str,
    latitude: float,
    longitude: float,
) -> Salon:
    async with async_session() as session:
        salon = Salon(
            name=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        session.add(salon)
        await session.commit()
        await session.refresh(salon)
        return salon


async def create_service(
    salon_id: int,
    category_id: int,
    name: str,
    price: int,
    duration_minutes: int,
) -> Service:
    async with async_session() as session:
        service = Service(
            salon_id=salon_id,
            category_id=category_id,
            name=name,
            price=price,
            duration_minutes=duration_minutes,
        )
        session.add(service)
        await session.commit()
        await session.refresh(service)
        return service


async def get_all_categories() -> list[Category]:
    async with async_session() as session:
        result = await session.execute(select(Category))
        return list(result.scalars().all())

async def create_pending_salon(name: str, address: str, latitude: float, longitude: float, owner_telegram_id: int) -> Salon:
    async with async_session() as session:
        salon = Salon(
            name=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            is_approved=False,
            owner_telegram_id=owner_telegram_id,
        )
        session.add(salon)
        await session.commit()
        await session.refresh(salon)
        return salon


async def approve_salon(salon_id: int) -> Salon | None:
    async with async_session() as session:
        result = await session.execute(select(Salon).where(Salon.id == salon_id))
        salon = result.scalar_one_or_none()
        if salon is None:
            return None
        salon.is_approved = True
        await session.commit()
        await session.refresh(salon)
        return salon


async def reject_salon(salon_id: int) -> Salon | None:
    async with async_session() as session:
        result = await session.execute(select(Salon).where(Salon.id == salon_id))
        salon = result.scalar_one_or_none()
        if salon is None:
            return None
        await session.delete(salon)
        await session.commit()
        return salon


async def get_salon_by_owner(owner_telegram_id: int) -> Salon | None:
    async with async_session() as session:
        result = await session.execute(
            select(Salon).where(Salon.owner_telegram_id == owner_telegram_id)
        )
        return result.scalar_one_or_none()