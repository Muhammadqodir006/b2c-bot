from datetime import datetime, timedelta

TASHKENT_OFFSET = timedelta(hours=5)


def to_utc(local_dt: datetime) -> datetime:
    """Toshkent vaqtini UTC'ga aylantiradi — bazaga yozishdan oldin ishlatiladi."""
    return local_dt - TASHKENT_OFFSET


def to_local(utc_dt: datetime) -> datetime:
    """Bazadagi UTC vaqtni Toshkent vaqtiga aylantiradi — foydalanuvchiga ko'rsatishdan oldin ishlatiladi."""
    return utc_dt + TASHKENT_OFFSET


def now_utc() -> datetime:
    """Hozirgi vaqtni UTC formatida qaytaradi — bronni yaratish, solishtirish uchun."""
    return datetime.utcnow()