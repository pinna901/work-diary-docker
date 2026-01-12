# utils package
from utils.decorators import validate_json
from utils.exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    ServiceUnavailableError
)

__all__ = ['validate_json', 'AppException', 'ValidationError', 'NotFoundError', 'ServiceUnavailableError', 'add']

# Keep the original add function for backward compatibility
def add(a, b):
    return a + b
