import redis.asyncio as redis
from config import settings

class RatingService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.leaderboard_key = "leaderboard"

    async def set_user_points(self, user_id: int, points: int):
        """Sets or updates the user's points in the leaderboard."""
        await self.redis_client.zadd(self.leaderboard_key, {str(user_id): points})

    async def increment_user_points(self, user_id: int, points: int) -> float:
        """Increments the user's points in the leaderboard."""
        return await self.redis_client.zincrby(self.leaderboard_key, points, str(user_id))

    async def get_top_10(self):
        """Returns the top 10 users from the leaderboard with their scores."""
        return await self.redis_client.zrange(
            self.leaderboard_key, 0, 9, desc=True, withscores=True
        )

    async def get_user_rank(self, user_id: int):
        """
        Returns the user's rank. Note: Redis rank is 0-based.
        If the user is not in the leaderboard, returns None.
        """
        rank = await self.redis_client.zrevrank(self.leaderboard_key, str(user_id))
        if rank is not None:
            return rank + 1  # Make it 1-based for human-readable output
        return None

    async def close(self):
        await self.redis_client.aclose()

rating_service = RatingService()
