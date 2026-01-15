from fastapi import FastAPI
from app.schemas import AddressRequest, AddressResponse

app = FastAPI(title="Address Validation Service")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/validate-address", response_model=AddressResponse)
async def validate_address(request: AddressRequest):
    # logic to be implemented
    return AddressResponse(address_raw=request.address_raw, valid=True, standardized=request.address_raw)
