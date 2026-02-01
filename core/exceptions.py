class DomainError(Exception):
    code: str = "ERROR"

    def __init__(self, message: str = None):
        self.message = message or "An error occurred"
        super().__init__(self.message)


class NotFound(DomainError):
    code = "NOT_FOUND"


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"


class AuthError(DomainError):
    code = "AUTH_ERROR"


class ConflictError(DomainError):
    code = "CONFLICT"


class ExternalServiceError(DomainError):
    code = "EXTERNAL_ERROR"
