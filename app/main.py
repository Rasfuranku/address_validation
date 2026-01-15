from fastapi import FastAPI, Depends
from app.schemas import AddressRequest, AddressResponse, StandardizedAddress
from app.services.validate_address_service import validate_address as validate_address_service
from app.services.input_processor import AddressInputProcessor
from app.core.dependencies import validate_api_key

app = FastAPI(
    title="Address Validation Service",
    description="Microservice to validate and standardize US addresses.",
    version="0.1.0",
)
input_processor = AddressInputProcessor()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/validate-address", response_model=AddressResponse, dependencies=[Depends(validate_api_key)])
async def validate_address(request: AddressRequest):
    # Step 1: Process Input (Sanitize, Validate, Normalize)
    processing_result = input_processor.process(request.address_raw)
    
    if not processing_result.is_valid:
        # Fail fast
        return AddressResponse(
            address_raw=request.address_raw,
            valid=False,
            standardized=None
        )

    # Step 2: External Validation (Smarty) using the sanitized input
    # We could also use processing_result.canonical_key for caching in the future
    result = validate_address_service(processing_result.sanitized_input)
    
    if result is None:
        return AddressResponse(address_raw=request.address_raw, valid=False, standardized=None)

    # Assuming 'result' contains standardized address information
    standardized_address = StandardizedAddress(
        street=result.delivery_line_1,
        city=result.components.city_name,
        state=result.components.state_abbreviation,
        zip_code=result.components.zipcode + "-" + result.components.plus4_code
    )
    return AddressResponse(address_raw=request.address_raw, valid=True, standardized=standardized_address)
