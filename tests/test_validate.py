import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app
from app.core.dependencies import validate_api_key, get_redis

from app.schemas import StandardizedAddress

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
    with patch("app.api.v1.endpoints.address.validate_address_service", new_callable=AsyncMock) as mock_service:
        # Mock return value from service
        mock_service.return_value = StandardizedAddress(
            street="123 Main St",
            city="Anytown",
            state="NY",
            zip_code="12345-6789"
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/v1/validate-address", json={"address_raw": "123 Main St"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "address_raw" in data["data"]
        assert data["data"]["valid"] is True
        assert data["data"]["standardized"]["street"] == "123 Main St"

@pytest.mark.asyncio
async def test_validate_address_invalid_input():
    # Test "Fail Fast" behavior (Input Processor catches this before Service/Redis)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Input too short (< 5 chars)
        response = await ac.post("/v1/validate-address", json={"address_raw": "123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["valid"] is False
    assert data["data"]["standardized"] is None
