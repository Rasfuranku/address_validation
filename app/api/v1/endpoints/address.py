from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from app.api.deps import get_redis, validate_api_key
from app.schemas import AddressRequest, AddressResponse, APIResponse, StandardizedAddress
from app.services.input_processor import AddressInputProcessor
from app.services.cache_service import AddressCacheService
from app.services.validate_address_service import validate_address as validate_address_service

router = APIRouter()
input_processor = AddressInputProcessor()

@router.post("/validate-address", response_model=APIResponse[AddressResponse], dependencies=[Depends(validate_api_key)])
async def validate_address(request: AddressRequest, redis: Redis = Depends(get_redis)):
    # Step 1: Process Input (Sanitize, Validate, Normalize)
    processing_result = input_processor.process(request.address_raw)
    
    if not processing_result.is_valid:
        # Fail fast
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
