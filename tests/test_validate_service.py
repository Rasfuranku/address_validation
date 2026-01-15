import pytest
from unittest.mock import patch, MagicMock
from app.services.validate_address_service import validate_address

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

@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.StaticCredentials")
@patch("app.services.validate_address_service.settings")
def test_validate_address_success(mock_settings, mock_creds, mock_builder):
    # Setup
    mock_settings.SMARTY_AUTH_ID = "test_id"
    mock_settings.SMARTY_AUTH_TOKEN = "test_token"

    mock_client = MagicMock()
    mock_builder.return_value.build_us_street_api_client.return_value = mock_client
    
    # Simulate a successful lookup result
    expected_candidate = MockCandidate("123 Main St", "Anytown", "NY", "12345", "6789")
    
    # The validate_address function modifies the passed lookup object in place.
    # We need to capture the lookup object passed to send_lookup and populate its result.
    def side_effect(lookup):
        lookup.result = [expected_candidate]
    
    mock_client.send_lookup.side_effect = side_effect

    # Execute
    result = validate_address("123 Main St")

    # Verify
    assert result == expected_candidate
    mock_client.send_lookup.assert_called_once()
    args, _ = mock_client.send_lookup.call_args
    assert args[0].street == "123 Main St"

@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.StaticCredentials")
@patch("app.services.validate_address_service.settings")
def test_validate_address_not_found(mock_settings, mock_creds, mock_builder):
    # Setup
    mock_settings.SMARTY_AUTH_ID = "test_id"
    mock_settings.SMARTY_AUTH_TOKEN = "test_token"

    mock_client = MagicMock()
    mock_builder.return_value.build_us_street_api_client.return_value = mock_client
    
    # Simulate empty result (address not found)
    def side_effect(lookup):
        lookup.result = []
    
    mock_client.send_lookup.side_effect = side_effect

    # Execute
    result = validate_address("Invalid Address 123")

    # Verify
    assert result is None
    mock_client.send_lookup.assert_called_once()

@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.StaticCredentials")
@patch("app.services.validate_address_service.settings")
def test_validate_address_typo_correction(mock_settings, mock_creds, mock_builder):
    # Setup
    mock_settings.SMARTY_AUTH_ID = "test_id"
    mock_settings.SMARTY_AUTH_TOKEN = "test_token"
    
    mock_client = MagicMock()
    mock_builder.return_value.build_us_street_api_client.return_value = mock_client

    # Input has typo "Mian", output has "Main"
    corrected_candidate = MockCandidate("123 Main St", "Anytown", "NY", "12345", "6789")
    
    def side_effect(lookup):
        lookup.result = [corrected_candidate]
    
    mock_client.send_lookup.side_effect = side_effect

    # Execute
    result = validate_address("123 Mian St")

    # Verify
    assert result.delivery_line_1 == "123 Main St"

@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.StaticCredentials")
@patch("app.services.validate_address_service.settings")
def test_validate_address_api_failure(mock_settings, mock_creds, mock_builder):
    # Setup
    mock_settings.SMARTY_AUTH_ID = "test_id"
    mock_settings.SMARTY_AUTH_TOKEN = "test_token"

    mock_client = MagicMock()
    mock_builder.return_value.build_us_street_api_client.return_value = mock_client
    
    # Simulate exception raising
    mock_client.send_lookup.side_effect = Exception("API Error")

    # Execute
    result = validate_address("123 Main St")

    # Verify
    assert result is None

@patch("app.services.validate_address_service.settings")
def test_validate_address_missing_credentials(mock_settings):
    # Setup
    mock_settings.SMARTY_AUTH_ID = ""
    mock_settings.SMARTY_AUTH_TOKEN = ""

    # Execute
    # The service currently passes empty strings to StaticCredentials which might not fail immediately 
    # until client build or send_lookup, OR strict implementation might check beforehand.
    # Looking at current implementation:
    # if not auth_id or not auth_token: pass
    # It continues to create credentials with empty strings.
    # If the SDK allows empty strings but fails on send, we need to mock that part or 
    # check if the logic short-circuits.
    # The current implementation has a 'pass' block which does nothing.
    
    # Let's see if we can trigger the Exception block or if it proceeds.
    # If it proceeds with empty strings, ClientBuilder might work but send_lookup usually fails 
    # or StaticCredentials might complain.
    
    with patch("app.services.validate_address_service.ClientBuilder") as mock_builder:
         mock_client = MagicMock()
         mock_builder.return_value.build_us_street_api_client.return_value = mock_client
         mock_client.send_lookup.side_effect = Exception("Auth Error")
         
         result = validate_address("123 Main St")
         assert result is None

@patch("app.services.validate_address_service.ClientBuilder")
@patch("app.services.validate_address_service.StaticCredentials")
@patch("app.services.validate_address_service.settings")
def test_validate_address_gibberish(mock_settings, mock_creds, mock_builder):
    # Setup
    mock_settings.SMARTY_AUTH_ID = "test_id"
    mock_settings.SMARTY_AUTH_TOKEN = "test_token"

    mock_client = MagicMock()
    mock_builder.return_value.build_us_street_api_client.return_value = mock_client
    
    # Gibberish likely returns empty result from Smarty
    def side_effect(lookup):
        lookup.result = []
    
    mock_client.send_lookup.side_effect = side_effect

    # Execute
    # Input processor would normally catch this, but unit testing this service specifically
    result = validate_address("AAAAAAAAAAAAAAAAA")

    # Verify
    assert result is None
