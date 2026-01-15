import hashlib
import json
import re
import logging
from redis.asyncio import Redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AddressCacheService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        # Pattern to keep only alphanumeric and spaces
        self.cleanup_pattern = re.compile(r'[^a-z0-9\s]')

    def generate_cache_key(self, address_raw: str) -> str:
        """
        Generates a smart cache key for the address.
        Strategy: Token Sorting.
        1. Lowercase and remove punctuation.
        2. Split into words.
        3. Sort words alphabetically.
        4. Join and hash.
        
        This allows inputs like "130 Jackson St 07055" and "07055 130 Jackson St" 
        to produce the same cache key, recognizing they are likely the same address.
        """
        # 1. Lowercase and strip non-alphanumeric (keep spaces)
        cleaned = self.cleanup_pattern.sub('', address_raw.lower())
        
        # 2. Split into tokens
        tokens = cleaned.split()
        
        # 3. Sort tokens alphabetically
        tokens.sort()
        
        # 4. Join them back together
        # Using simple concatenation to form the basis for the hash
        sorted_str = "".join(tokens)
        
        # 5. Return SHA-256 hash
        return hashlib.sha256(sorted_str.encode('utf-8')).hexdigest()

    async def get_cached_address(self, address_raw: str):
        key = self.generate_cache_key(address_raw)
        try:
            data = await self.redis.get(key)
            if data:
                logger.info("Cache HIT for key: %s", key)
                return json.loads(data)
            logger.info("Cache MISS for key: %s", key)
        except Exception as e:
            # Resilience: Log error and return None (fail open)
            logger.warning("Redis connection failed: %s", e)
            return None
        return None

    async def cache_address(self, address_raw: str, data: dict | BaseModel):
        key = self.generate_cache_key(address_raw)
        
        if isinstance(data, BaseModel):
            value = data.model_dump_json()
        else:
            value = json.dumps(data)
            
        try:
            # TTL: 30 days = 2,592,000 seconds
            await self.redis.set(key, value, ex=2592000)
        except Exception as e:
            # Resilience: Log error and continue
            logger.warning("Redis set failed: %s", e)
