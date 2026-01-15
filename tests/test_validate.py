import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_validate_address():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/validate-address", json={"address_raw": "123 Main St"})
    
    # We expect 200 OK
    assert response.status_code == 200
    data = response.json()
    assert "address_raw" in data
    # If the logic is implemented, standardized might be a dict now
    if data.get("valid"):
        assert isinstance(data["standardized"], dict)
        assert "street" in data["standardized"]

@pytest.mark.asyncio
async def test_validate_address_invalid_input():
    # Test "Fail Fast" behavior
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Input too short (< 5 chars)
        response = await ac.post("/validate-address", json={"address_raw": "123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["standardized"] is None
