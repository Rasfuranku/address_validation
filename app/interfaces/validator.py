from abc import ABC, abstractmethod
from app.schemas import StandardizedAddress

class AddressValidator(ABC):
    @abstractmethod
    async def validate(self, address: str) -> StandardizedAddress | None:
        pass
