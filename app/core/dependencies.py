from redis.asyncio import Redis
from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.core.config import settings
from app.core.security import hash_key

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_redis() -> Redis:
    redis = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()

async def validate_api_key(
    key: str = Security(api_key_header),
    redis: Redis = Depends(get_redis)
) -> str:
    if key is None:
        raise HTTPException(status_code=403, detail="Missing API Key")
    
    hashed = hash_key(key)
    exists = await redis.sismember("allowed_api_key_hashes", hashed)
    
    if not exists:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    return key
