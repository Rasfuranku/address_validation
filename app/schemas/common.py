from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: int
    message: str
    type: str

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
