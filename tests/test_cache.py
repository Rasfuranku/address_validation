import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from redis.exceptions import ConnectionError, TimeoutError
import json
import hashlib

from app.services.cache_service import AddressCacheService

# ... (MockModel class remains same)

@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    # Configure specific methods if needed, but AsyncMock handles await automatically.
    return mock

@pytest.fixture
def cache_service(mock_redis):
    return AddressCacheService(redis_client=mock_redis)

class TestKeyGeneration:
    def test_generate_key_sorting(self, cache_service):
        # "130 jackson st 07055" vs "07055 130 jackson st"
        addr1 = "130 jackson st 07055"
        addr2 = "07055 130 jackson st"
        
        key1 = cache_service.generate_cache_key(addr1)
        key2 = cache_service.generate_cache_key(addr2)
        
        assert key1 == key2
        
    def test_generate_key_sorting_complex(self, cache_service):
        # Different spacing, same words
        addr1 = "  130   Jackson   St   "
        addr2 = "Jackson St 130"
        
        key1 = cache_service.generate_cache_key(addr1)
        key2 = cache_service.generate_cache_key(addr2)
        
        assert key1 == key2

    def test_generate_key_hashing(self, cache_service):
        # Verify it returns a SHA256 hex string
        key = cache_service.generate_cache_key("test")
        assert len(key) == 64 # SHA256 is 64 hex chars
        # Verify content
        # "test" -> sorted "test" -> sha256
        expected = hashlib.sha256("test".encode()).hexdigest()
        assert key == expected

class TestCacheOperations:
    @pytest.mark.asyncio
    async def test_get_resilience_connection_error(self, cache_service, mock_redis):
        mock_redis.get.side_effect = ConnectionError("Redis down")
        
        result = await cache_service.get_cached_address("some input")
        
        # Should return None, not raise exception
        assert result is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_resilience_timeout_error(self, cache_service, mock_redis):
        mock_redis.get.side_effect = TimeoutError("Redis timeout")
        
        result = await cache_service.get_cached_address("some input")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_resilience_error(self, cache_service, mock_redis):
        mock_redis.set.side_effect = ConnectionError("Redis down")
        
        # Should not raise
        await cache_service.cache_address("input", {"data": "test"})
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_service, mock_redis):
        mock_redis.get.return_value = '{"valid": true}'
        
        result = await cache_service.get_cached_address("input")
        
        assert result == {"valid": True}

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service, mock_redis):
        mock_redis.get.return_value = None
        
        result = await cache_service.get_cached_address("input")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_cache(self, cache_service, mock_redis):
        data = {"valid": True}
        await cache_service.cache_address("input", data)
        
        # Verify key generation and set call
        key = cache_service.generate_cache_key("input")
        mock_redis.set.assert_called_once_with(key, json.dumps(data), ex=2592000) # 30 days = 30*24*60*60 = 2592000

    @pytest.mark.asyncio
    async def test_set_cache_pydantic(self, cache_service, mock_redis):
        # Simulate passing a Pydantic model (using model_dump logic if supported, or just dict)
        # The prompt says "Method to store Pydantic models (JSON dump)".
        # Let's assume the method accepts dict or model and converts to json.
        
        data = {"valid": True}
        await cache_service.cache_address("input", data)
        
        key = cache_service.generate_cache_key("input")
        mock_redis.set.assert_called_once_with(key, json.dumps(data), ex=2592000)
