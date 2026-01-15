import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.core.dependencies import validate_api_key, get_redis

@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.incr.return_value = 1
    return mock

@pytest.fixture(autouse=True)
def override_deps(mock_redis):
    app.dependency_overrides[validate_api_key] = lambda: "test_key"
    app.dependency_overrides[get_redis] = lambda: mock_redis
    yield
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_validate_address(mock_redis):
    # Patch the service call to avoid real API/Redis logic in this integration test
    with patch("app.main.validate_address_service", new_callable=AsyncMock) as mock_service:
        # Mock return value from service
        mock_result = MagicMock()
        mock_result.delivery_line_1 = "123 Main St"
        mock_result.components.city_name = "Anytown"
        mock_result.components.state_abbreviation = "NY"
        mock_result.components.zipcode = "12345"
        mock_result.components.plus4_code = "6789"
        mock_service.return_value = mock_result

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/validate-address", json={"address_raw": "123 Main St"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["standardized"]["street"] == "123 Main St"

@pytest.mark.asyncio
async def test_validate_address_invalid_input():
    # Test "Fail Fast" behavior (Input Processor catches this before Service/Redis)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Input too short (< 5 chars)
        response = await ac.post("/validate-address", json={"address_raw": "123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["standardized"] is None
