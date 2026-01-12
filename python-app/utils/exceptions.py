# Custom exceptions

class AppException(Exception):
    """应用基础异常"""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class ValidationError(AppException):
    """数据验证错误"""
    def __init__(self, message):
        super().__init__(message, status_code=400)

class NotFoundError(AppException):
    """资源未找到错误"""
    def __init__(self, message):
        super().__init__(message, status_code=404)

class ServiceUnavailableError(AppException):
    """服务不可用错误"""
    def __init__(self, message):
        super().__init__(message, status_code=503)
