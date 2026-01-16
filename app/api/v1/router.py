from fastapi import APIRouter
from app.api.v1.endpoints import address, health

api_router = APIRouter()
# Health check often lives at root or /health, not /api/v1/health, but requirements say "Move... logic to app/api/v1/endpoints/health.py".
# And "Router inclusion: app.include_router(api_v1_router, prefix='/api/v1')".
# This implies /api/v1/health.
# I'll stick to that.
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(address.router, tags=["address"])
