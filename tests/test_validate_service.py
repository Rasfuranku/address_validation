import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.validate_address_service import validate_address
from app.core.exceptions import DailyQuotaExceededError

# Mock structure for a Smarty Candidate
class MockCandidate:
    def __init__(self, delivery_line_1, city, state, zipcode, plus4_code):
        self.delivery_line_1 = delivery_line_1
        self.components = MagicMock()
        self.components.city_name = city
        self.components.state_abbreviation = state
        self.components.zipcode = zipcode
        self.components.plus4_code = plus4_code
        self.last_line = f"{city} {state} {zipcode}-{plus4_code}"
        self.analysis = MagicMock()
        self.analysis.dpv_match_code = "Y"

@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    # Default: Quota is 1 (safe)
    mock.incr.return_value = 1
    return mock

@pytest.mark.asyncio
@patch("app.services.validate_address_service.usaddress.parse")
@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.StaticCredentials")
@patch("app.services.validate_address_service.settings")
async def test_validate_address_success(mock_settings, mock_creds, mock_builder, mock_usaddress_parse, mock_redis):
    # Setup
    mock_settings.SMARTY_AUTH_ID = "test_id"
    mock_settings.SMARTY_AUTH_TOKEN = "test_token"
    mock_settings.SMARTY_DAILY_LIMIT = 33

    mock_client = MagicMock()
    mock_builder.return_value.build_us_street_api_client.return_value = mock_client
    
    # Mock usaddress parsing result
    mock_usaddress_parse.return_value = [
        ('123', 'AddressNumber'),
        ('Main', 'StreetName'),
        ('St', 'StreetNamePostType'),
        ('Anytown', 'PlaceName'),
        ('NY', 'StateName'),
        ('12345', 'ZipCode')
    ]

    expected_candidate = MockCandidate("123 Main St", "Anytown", "NY", "12345", "6789")
    
    def side_effect(lookup):
        lookup.result = [expected_candidate]
    
    mock_client.send_lookup.side_effect = side_effect

    # Execute
    result = await validate_address("123 Main St", mock_redis)

    # Verify
    assert result == expected_candidate
    mock_client.send_lookup.assert_called_once()
    mock_redis.incr.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.settings")
async def test_daily_limit_exceeded(mock_settings, mock_builder, mock_redis):
    mock_settings.SMARTY_DAILY_LIMIT = 33
    # Mock redis increment returning > limit
    mock_redis.incr.return_value = 34

    # Execute & Verify
    with pytest.raises(DailyQuotaExceededError):
        await validate_address("123 Main St", mock_redis)
    
    # Verify Smarty client was NOT built/called
    mock_builder.assert_not_called()
    # Verify decrement was called to revert the count
    mock_redis.decr.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.StaticCredentials")
@patch("app.services.validate_address_service.settings")
async def test_validate_address_not_found(mock_settings, mock_creds, mock_builder, mock_redis):
    mock_settings.SMARTY_DAILY_LIMIT = 33
    mock_client = MagicMock()
    mock_builder.return_value.build_us_street_api_client.return_value = mock_client
    
    def side_effect(lookup):
        lookup.result = []
    
    mock_client.send_lookup.side_effect = side_effect

    result = await validate_address("Invalid Address 123", mock_redis)

    assert result is None
    mock_client.send_lookup.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.StaticCredentials")
@patch("app.services.validate_address_service.settings")
async def test_validate_address_api_failure(mock_settings, mock_creds, mock_builder, mock_redis):
    mock_settings.SMARTY_DAILY_LIMIT = 33
    mock_client = MagicMock()
    mock_builder.return_value.build_us_street_api_client.return_value = mock_client
    
    mock_client.send_lookup.side_effect = Exception("API Error")

    result = await validate_address("123 Main St", mock_redis)

    assert result is None

@patch("app.services.validate_address_service.settings")
@pytest.mark.asyncio
async def test_validate_address_missing_credentials(mock_settings, mock_redis):
    mock_settings.SMARTY_DAILY_LIMIT = 33
    mock_settings.SMARTY_AUTH_ID = ""
    mock_settings.SMARTY_AUTH_TOKEN = ""

    with patch("app.services.validate_address_service.ClientBuilder") as mock_builder:
         mock_client = MagicMock()
         mock_builder.return_value.build_us_street_api_client.return_value = mock_client
         mock_client.send_lookup.side_effect = Exception("Auth Error")
         
         result = await validate_address("123 Main St", mock_redis)
         assert result is None
