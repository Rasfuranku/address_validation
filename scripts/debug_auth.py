import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_key
from app.core.config import settings
from redis.asyncio import Redis

async def debug_check(raw_key: str):
    print(f"Checking key: {raw_key}")
    
    # 1. Compute Hash
    hashed = hash_key(raw_key)
    print(f"Computed Hash: {hashed}")
    
    # 2. Check Redis
    print(f"Connecting to Redis at: {settings.REDIS_URL}")
    redis = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    
    try:
        exists = await redis.sismember("allowed_api_key_hashes", hashed)
        print(f"Redis sismember result: {exists}")
        
        # List all members to be sure
        members = await redis.smembers("allowed_api_key_hashes")
        print(f"All allowed hashes in Redis: {members}")
        
        if hashed in members:
            print("✅ Match found in set member list.")
        else:
            print("❌ No match in set member list.")
            
    except Exception as e:
        print(f"Redis Error: {e}")
    finally:
        await redis.aclose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/debug_auth.py <raw_key>")
        sys.exit(1)
    
    raw_key = sys.argv[1]
    asyncio.run(debug_check(raw_key))
