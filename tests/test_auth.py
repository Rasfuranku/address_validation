import pytest
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from app.core.dependencies import get_redis, validate_api_key
import hashlib

# Create a dummy app for testing the dependency
app = FastAPI()

@app.get("/protected")
async def protected_endpoint(valid: bool = Depends(validate_api_key)):
    return {"message": "Access Granted"}

client = TestClient(app)

# Helper to generate hash
def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    return mock

# Override the get_redis dependency
@pytest.fixture(autouse=True)
def override_redis(mock_redis):
    app.dependency_overrides[get_redis] = lambda: mock_redis
    yield
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_auth_missing_header(mock_redis):
    # Should fail if header is missing
    response = client.get("/protected")
    assert response.status_code == 403
    assert response.json() == {"detail": "Missing API Key"}

@pytest.mark.asyncio
async def test_auth_invalid_key(mock_redis):
    # Setup Redis to return 0 (False) for sismember
    mock_redis.sismember.return_value = 0
    
    response = client.get("/protected", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid API Key"}
    
    # Verify checking logic
    mock_redis.sismember.assert_called_once()

@pytest.mark.asyncio
async def test_auth_valid_key(mock_redis):
    # Valid key
    raw_key = "addr_vk_validkey123"
    hashed_key = hash_key(raw_key)
    
    # Setup Redis to return 1 (True) when checking this hash
    # sismember(name, value)
    def side_effect(name, value):
        if name == "allowed_api_key_hashes" and value == hashed_key:
            return 1
        return 0
    
    mock_redis.sismember.side_effect = side_effect
    
    response = client.get("/protected", headers={"X-API-Key": raw_key})
    assert response.status_code == 200
    assert response.json() == {"message": "Access Granted"}

@pytest.mark.asyncio
async def test_auth_extra_headers_ignored(mock_redis):
    # Valid key with extra headers
    raw_key = "addr_vk_validkey123"
    hashed_key = hash_key(raw_key)
    mock_redis.sismember.return_value = 1
    
    response = client.get("/protected", headers={
        "X-API-Key": raw_key,
        "X-Extra-Header": "somevalue"
    })
    assert response.status_code == 200
