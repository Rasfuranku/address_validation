import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.exceptions import ProviderTimeoutError, AddressProviderError, DailyQuotaExceededError
from app.core.dependencies import validate_api_key, get_redis
from unittest.mock import AsyncMock, patch

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture(autouse=True)
def override_deps():
    app.dependency_overrides[validate_api_key] = lambda: "test_key"
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 1
    mock_redis.get.return_value = None # Cache miss by default
    app.dependency_overrides[get_redis] = lambda: mock_redis
    yield
    app.dependency_overrides = {}

def assert_error_response(response, status_code, error_type_fragment):
    # status_code check
    assert response.status_code == status_code
    data = response.json()
    
    # Standardized Schema check
    assert "success" in data
    assert data["success"] is False
    assert "error" in data
    assert data["error"] is not None
    assert "code" in data["error"]
    assert data["error"]["code"] == status_code
    assert "type" in data["error"]
    assert error_type_fragment in data["error"]["type"]

@pytest.mark.asyncio
async def test_timeout_error():
    # Patch the service to raise the custom exception
    # Assuming refactoring maps this exception
    with patch("app.main.validate_address_service", side_effect=ProviderTimeoutError("Timeout")):
        response = client.post("/validate-address", json={"address_raw": "123 Timeout"})
        assert_error_response(response, 504, "provider_timeout")

@pytest.mark.asyncio
async def test_provider_error():
    with patch("app.main.validate_address_service", side_effect=AddressProviderError("Upstream Error")):
        response = client.post("/validate-address", json={"address_raw": "123 Error"})
        assert_error_response(response, 502, "provider_error")

@pytest.mark.asyncio
async def test_quota_error():
    with patch("app.main.validate_address_service", side_effect=DailyQuotaExceededError("Quota")):
        response = client.post("/validate-address", json={"address_raw": "123 Quota"})
        assert_error_response(response, 429, "quota_exceeded")

@pytest.mark.asyncio
async def test_validation_error():
    # Missing field
    response = client.post("/validate-address", json={})
    # Pydantic raises RequestValidationError
    # We want standardized response
    assert response.status_code == 422 # Default FastAPI, unless mapped to 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "validation_error"

@pytest.mark.asyncio
async def test_generic_exception():
    with patch("app.main.validate_address_service", side_effect=Exception("Boom")):
        response = client.post("/validate-address", json={"address_raw": "123 Boom"})
        assert_error_response(response, 500, "server_error")
