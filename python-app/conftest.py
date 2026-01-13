"""
Pytest 全局配置文件
这个文件会自动被 pytest 加载，用于配置所有测试
"""
import pytest
import os
import sys

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

# 设置测试环境变量（在导入 app 之前）
os. environ['TESTING'] = 'true'
os.environ['FLASK_ENV'] = 'testing'
os.environ['MYSQL_ROOT_PASSWORD'] = 'test'
os.environ['DB_HOST'] = 'localhost'
os.environ['MYSQL_DATABASE'] = 'test_db'

@pytest.fixture(scope='function')
def app():
    """
    创建测试应用
    scope='function' 表示每个测试函数都会创建新的 app
    """
    from app import create_app
    
    # 创建应用实例
    test_app = create_app('development')
    
    # 设置测试模式
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # 使用内存数据库
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return test_app

@pytest.fixture(scope='function')
def client(app):
    """
    创建测试客户端
    用于发送 HTTP 请求
    """
    return app.test_client()

@pytest.fixture(scope='function')
def mock_redis():
    """
    创建 Mock Redis 客户端
    避免测试时真的连接 Redis
    """
    from unittest.mock import Mock
    
    redis_mock = Mock()
    redis_mock.incr = Mock(return_value=42)
    redis_mock.ping = Mock(return_value=True)
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock(return_value=True)
    
    return redis_mock

@pytest.fixture(scope='function')
def mock_db_session():
    """
    创建 Mock 数据库会话
    避免测试时真的操作数据库
    """
    from unittest.mock import Mock, patch
    
    with patch('models.db.session') as mock_session:
        mock_session. add = Mock()
        mock_session.commit = Mock()
        mock_session. rollback = Mock()
        mock_session.remove = Mock()
        yield mock_session