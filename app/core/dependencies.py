from redis.asyncio import Redis
from app.core.config import settings

async def get_redis() -> Redis:
    redis = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()
