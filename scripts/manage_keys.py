import asyncio
import argparse
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import generate_key
from app.core.config import settings
from redis.asyncio import Redis

async def add_key_to_redis(hashed_key: str):
    """Adds the hashed key to the Redis set."""
    redis = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        await redis.sadd("allowed_api_key_hashes", hashed_key)
        print(f"✅ Hashed key added to Redis set 'allowed_api_key_hashes'.")
    except Exception as e:
        print(f"❌ Error adding to Redis: {e}")
    finally:
        await redis.aclose()

def main():
    parser = argparse.ArgumentParser(description="Manage API Keys for Address Validation Service")
    parser.add_argument("--add", action="store_true", help="Automatically add the hash to Redis")
    args = parser.parse_args()

    print("Generating new API Key...")
    raw_key, key_hash = generate_key()
    
    print("\n" + "="*60)
    print(f"🔑 RAW API KEY: {raw_key}")
    print("="*60)
    print("⚠️  SAVE THIS KEY NOW! It will not be shown again.")
    print(f"🔒 Key Hash (SHA-256): {key_hash}")
    print("="*60 + "\n")

    if args.add:
        asyncio.run(add_key_to_redis(key_hash))
    else:
        print("Run with --add to automatically add the hash to Redis.")

if __name__ == "__main__":
    main()
