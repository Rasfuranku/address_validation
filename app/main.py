from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.schemas import AddressRequest, AddressResponse, StandardizedAddress
from app.services.validate_address_service import validate_address as validate_address_service
from app.services.input_processor import AddressInputProcessor
from app.services.cache_service import AddressCacheService
from app.core.dependencies import validate_api_key, get_redis
from app.core.exceptions import DailyQuotaExceededError
from app.core.logging import setup_logging
from redis.asyncio import Redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield

app = FastAPI(
    title="Address Validation Service",
    description="Microservice to validate and standardize US addresses.",
    version="0.1.0",
    lifespan=lifespan
)
input_processor = AddressInputProcessor()

@app.exception_handler(DailyQuotaExceededError)
async def quota_exceeded_handler(request: Request, exc: DailyQuotaExceededError):
    return JSONResponse(
        status_code=429,
        content={"detail": "Daily validation quota exceeded. Please try again tomorrow."},
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/validate-address", response_model=AddressResponse, dependencies=[Depends(validate_api_key)])
async def validate_address(request: AddressRequest, redis: Redis = Depends(get_redis)):
    # Step 1: Process Input (Sanitize, Validate, Normalize)
    processing_result = input_processor.process(request.address_raw)
    
    if not processing_result.is_valid:
        # Fail fast
        return AddressResponse(
            address_raw=request.address_raw,
            valid=False,
            standardized=None
        )

    # Step 2: Caching Layer
    # Use sanitized input for cache key generation to ensure consistency
    cache_service = AddressCacheService(redis)
    cached_data = await cache_service.get_cached_address(processing_result.sanitized_input)
    
    if cached_data:
        # Cache Hit
        standardized_address = StandardizedAddress(**cached_data)
        return AddressResponse(
            address_raw=request.address_raw, 
            valid=True, 
            standardized=standardized_address
        )

    # Step 3: External Validation (Smarty)
    result = await validate_address_service(processing_result.sanitized_input, redis)
    
    if result is None:
        return AddressResponse(address_raw=request.address_raw, valid=False, standardized=None)

    # Assuming 'result' contains standardized address information
    standardized_address = StandardizedAddress(
        street=result.delivery_line_1,
        city=result.components.city_name,
        state=result.components.state_abbreviation,
        zip_code=result.components.zipcode + "-" + result.components.plus4_code
    )
    
    # Step 4: Store in Cache
    await cache_service.cache_address(processing_result.sanitized_input, standardized_address)
    
    return AddressResponse(address_raw=request.address_raw, valid=True, standardized=standardized_address)
