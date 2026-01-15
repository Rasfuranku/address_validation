import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.cache_service import AddressCacheService
from app.main import validate_address
from app.schemas import AddressRequest

@pytest.mark.asyncio
@patch("app.main.validate_address_service")
@patch("app.main.input_processor")
async def test_caching_logic(mock_processor, mock_validate_service):
    # Setup
    mock_redis = AsyncMock()
    
    # Mock Input Processing
    mock_processor.process.return_value.is_valid = True
    mock_processor.process.return_value.sanitized_input = "123 Main St"
    
    # Scenario 1: Cache Miss
    # Redis get returns None
    mock_redis.get.return_value = None
    
    # Mock Service Result (Candidate)
    mock_candidate = MagicMock()
    mock_candidate.delivery_line_1 = "123 Main St"
    mock_candidate.components.city_name = "City"
    mock_candidate.components.state_abbreviation = "ST"
    mock_candidate.components.zipcode = "12345"
    mock_candidate.components.plus4_code = "6789"
    mock_validate_service.return_value = mock_candidate
    
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
    
    assert response.standardized.city == "City"
