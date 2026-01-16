import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.cache_service import AddressCacheService
from app.api.v1.endpoints.address import validate_address
from app.schemas import AddressRequest, StandardizedAddress

@pytest.mark.asyncio
@patch("app.api.v1.endpoints.address.validate_address_service")
@patch("app.api.v1.endpoints.address.input_processor")
async def test_caching_logic(mock_processor, mock_validate_service):
    # Setup
    mock_redis = AsyncMock()
    
    # Mock Input Processing
    mock_processor.process.return_value.is_valid = True
    mock_processor.process.return_value.sanitized_input = "123 Main St"
    
    # Scenario 1: Cache Miss
    # Redis get returns None
    mock_redis.get.return_value = None
    
    # Mock Service Result (StandardizedAddress)
    mock_validate_service.return_value = StandardizedAddress(
        street="123 Main St",
        city="City",
        state="ST",
        zip_code="12345-6789"
    )
    
    request = AddressRequest(address_raw="123 Main St")
    
    # Execute Miss
    response = await validate_address(request, mock_redis)
    
    # Verify Miss Behavior
    mock_redis.get.assert_called_once() # Checked cache
    mock_validate_service.assert_called_once() # Called service
    mock_redis.set.assert_called_once() # Set cache
    
    # Reset mocks for Scenario 2
    mock_redis.reset_mock()
    mock_validate_service.reset_mock()
    
    # Scenario 2: Cache Hit
    # Redis get returns JSON string
    cached_json = '{"street": "123 Main St", "city": "City", "state": "ST", "zip_code": "12345-6789"}'
    mock_redis.get.return_value = cached_json
    
    # Execute Hit
    response = await validate_address(request, mock_redis)
    
    # Verify Hit Behavior
    mock_redis.get.assert_called_once() # Checked cache
    mock_validate_service.assert_not_called() # SHOULD NOT CALL SERVICE
    mock_redis.set.assert_not_called() # No need to set
    
    assert response.success is True
    assert response.data.standardized.city == "City"
