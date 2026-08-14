import math

from database.repositories.salon_repo import get_all_salons


def calculate_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Ikki koordinata orasidagi masofani kilometrda hisoblaydi."""
    earth_radius_km = 6371.0

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius_km * c


async def get_nearby_salons(
    user_lat: float,
    user_lon: float,
    radius_km: float = 3.0,
):
    salons = await get_all_salons()

    nearby = []
    for salon in salons:
        distance = calculate_distance_km(
            user_lat,
            user_lon,
            salon.latitude,
            salon.longitude,
        )

        if distance <= radius_km:
            nearby.append((salon, distance))

    nearby.sort(key=lambda item: item[1])
    return nearby
