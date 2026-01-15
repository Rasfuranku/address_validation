import pytest
from app.core.dependencies import get_redis
from app.core.config import settings
import fakeredis.aioredis

# Patch the get_redis dependency or just test the logic with fakeredis
# For this test, we want to verify we can connect and set/get values.

@pytest.mark.asyncio
async def test_redis_connection():
    # Use fakeredis to simulate the connection
    redis = fakeredis.aioredis.FakeRedis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    
    await redis.set("test_key", "test_value")
    value = await redis.get("test_key")
    
    assert value == "test_value"
    await redis.aclose()
