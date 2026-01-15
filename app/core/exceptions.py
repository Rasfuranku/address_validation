class AppException(Exception):
    def __init__(self, message: str, status_code: int, error_code: str):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class DailyQuotaExceededError(AppException):
    def __init__(self, message: str = "Daily quota exceeded"):
        super().__init__(message, 429, "quota_exceeded")

class AddressProviderError(AppException):
    def __init__(self, message: str = "Provider unavailable"):
        super().__init__(message, 502, "provider_error")

class ProviderTimeoutError(AppException):
    def __init__(self, message: str = "Provider timed out"):
        super().__init__(message, 504, "provider_timeout")

class InputValidationError(AppException):
    def __init__(self, message: str = "Invalid input"):
        super().__init__(message, 400, "validation_error")
