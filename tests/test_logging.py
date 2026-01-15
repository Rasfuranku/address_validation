import logging
import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from app.core.logging import setup_logging
from app.services.cache_service import AddressCacheService
from app.services.validate_address_service import validate_address

def test_setup_logging(capsys):
    setup_logging()
    logger = logging.getLogger("test_logger")
    logger.info("Test Info Message")
    
    captured = capsys.readouterr()
    assert "Test Info Message" in captured.err

@pytest.mark.asyncio
async def test_cache_service_logging(capsys):
    setup_logging()
    
    mock_redis = AsyncMock()
    service = AddressCacheService(mock_redis)
    
    # Test Cache Miss Log
    mock_redis.get.return_value = None
    await service.get_cached_address("test_miss")
    
    captured = capsys.readouterr()
    assert "Cache MISS" in captured.err

    # Test Cache Hit Log
    mock_redis.get.return_value = '{"valid": true}'
    await service.get_cached_address("test_hit")
    
    captured = capsys.readouterr()
    assert "Cache HIT" in captured.err

    # Test Redis Error Log
    mock_redis.get.side_effect = Exception("Redis Down")
    await service.get_cached_address("test_error")
    
    captured = capsys.readouterr()
    assert "Redis connection failed" in captured.err
    
