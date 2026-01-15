from fastapi import FastAPI
from app.schemas import AddressRequest, AddressResponse
from app.services.validate_address_service import validate_address as validate_address_service

app = FastAPI(title="Address Validation Service")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/validate-address", response_model=AddressResponse)
async def validate_address(request: AddressRequest):
    result = validate_address_service(request.address_raw)
    if result is None:
        return AddressResponse(address_raw=request.address_raw, valid=False, standardized=None)

    standardized_address = {
        "street": result.delivery_line_1,
        "city": result.components.city_name,
        "state": result.components.state_abbreviation,
        "zip_code": result.components.zipcode + "-" + result.components.plus4_code
    }
    return AddressResponse(address_raw=request.address_raw, valid=True, standardized=standardized_address)
