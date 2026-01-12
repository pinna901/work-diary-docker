# Custom exceptions

class AppException(Exception):
    """
    Base application exception.
    应用基础异常
    """
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class ValidationError(AppException):
    """
    Data validation error.
    数据验证错误
    """
    def __init__(self, message):
        super().__init__(message, status_code=400)

class NotFoundError(AppException):
    """
    Resource not found error.
    资源未找到错误
    """
    def __init__(self, message):
        super().__init__(message, status_code=404)

class ServiceUnavailableError(AppException):
    """
    Service unavailable error.
    服务不可用错误
    """
    def __init__(self, message):
        super().__init__(message, status_code=503)
