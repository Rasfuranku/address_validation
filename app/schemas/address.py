from pydantic import BaseModel

class AddressRequest(BaseModel):
    address_raw: str

class StandardizedAddress(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str

class AddressResponse(BaseModel):
    address_raw: str
    standardized: StandardizedAddress | None = None
    valid: bool = False
