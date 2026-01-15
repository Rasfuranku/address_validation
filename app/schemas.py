from pydantic import BaseModel

class AddressRequest(BaseModel):
    address_raw: str

class AddressResponse(BaseModel):
    address_raw: str
    standardized: str | None = None
    valid: bool = False
