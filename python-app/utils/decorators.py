# Custom decorators
from functools import wraps

def validate_json(f):
    """
    Validates that the request contains valid JSON data.
    验证请求包含有效的 JSON 数据
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function
