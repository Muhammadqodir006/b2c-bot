from sqlalchemy import select

from database.engine import async_session
from database.models import Service
from database.repositories.salon_repo import (
    get_salons_by_category as repo_get_salons_by_category,
)


async def get_salons_by_category(category_id: int):
    return await repo_get_salons_by_category(category_id)