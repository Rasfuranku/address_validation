from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

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

class ErrorDetail(BaseModel):
    code: int
    message: str
    type: str

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
