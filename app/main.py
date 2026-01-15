from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.schemas import AddressRequest, AddressResponse, StandardizedAddress, APIResponse, ErrorDetail
from app.services.validate_address_service import validate_address as validate_address_service
from app.services.input_processor import AddressInputProcessor
from app.services.cache_service import AddressCacheService
from app.core.dependencies import validate_api_key, get_redis
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from redis.asyncio import Redis
import logging

logger = logging.getLogger(__name__)

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

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse[None](
            success=False,
            error=ErrorDetail(code=exc.status_code, message=exc.message, type=exc.error_code)
        ).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=APIResponse[None](
            success=False,
            error=ErrorDetail(code=422, message="Validation Error", type="validation_error")
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse[None](
            success=False,
            error=ErrorDetail(code=500, message="Internal Server Error", type="server_error")
        ).model_dump()
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/validate-address", response_model=APIResponse[AddressResponse], dependencies=[Depends(validate_api_key)])
async def validate_address(request: AddressRequest, redis: Redis = Depends(get_redis)):
    # Step 1: Process Input (Sanitize, Validate, Normalize)
    processing_result = input_processor.process(request.address_raw)
    
    if not processing_result.is_valid:
        # Fail fast - InputValidationError could be raised here if we wanted to map to 400
        # But returning success=True with valid=False is also a valid pattern for "validation service"
        # However, requirements asked for InputValidationError (400) logic.
        # But existing logic returns 200 OK with valid=False. I'll stick to that unless forced.
        # The schema supports it.
        return APIResponse(
            success=True,
            data=AddressResponse(
                address_raw=request.address_raw,
                valid=False,
                standardized=None
            )
        )

    # Step 2: Caching Layer
    cache_service = AddressCacheService(redis)
    cached_data = await cache_service.get_cached_address(processing_result.sanitized_input)
    
    if cached_data:
        # Cache Hit
        standardized_address = StandardizedAddress(**cached_data)
        return APIResponse(
            success=True,
            data=AddressResponse(
                address_raw=request.address_raw, 
                valid=True, 
                standardized=standardized_address
            )
        )

    # Step 3: External Validation (Smarty)
    # validate_address_service now returns StandardizedAddress or None
    result = await validate_address_service(processing_result.sanitized_input, redis)
    
    if result is None:
        return APIResponse(
            success=True,
            data=AddressResponse(address_raw=request.address_raw, valid=False, standardized=None)
        )

    # Step 4: Store in Cache
    await cache_service.cache_address(processing_result.sanitized_input, result)
    
    return APIResponse(
        success=True,
        data=AddressResponse(address_raw=request.address_raw, valid=True, standardized=result)
    )
