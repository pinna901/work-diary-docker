# config.py
import os
from datetime import timedelta

class BaseConfig:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
    
    # 数据库配置
    MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD', '0901')
    DB_HOST = os.getenv('DB_HOST', 'db')
    DB_NAME = os.getenv('MYSQL_DATABASE', 'work_diary_db')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:{MYSQL_ROOT_PASSWORD}@{DB_HOST}/{DB_NAME}'
    
    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # 缓存配置
    CACHE_DEFAULT_TTL = 300  # 5 分钟
    CACHE_DIARY_LIST_TTL = 300
    CACHE_QUOTE_TTL = 86400  # 24 小时
    
    # AI 服务配置
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = 'llama-3.3-70b-versatile'
    GROQ_TIMEOUT = 10

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 3600

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
