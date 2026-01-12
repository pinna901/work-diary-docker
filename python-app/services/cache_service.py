import redis
import json
import hashlib
import logging
from functools import wraps
from typing import Any, Optional

logger = logging.getLogger(__name__)

class CacheService:
    """缓存服务"""
    
    def __init__(self, redis_host='redis', redis_port=6379, redis_db=0):
        try:
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            self.redis.ping()
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.enabled = False
        
        self.default_ttl = 300
        self.stats = {'hits': 0, 'misses': 0}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                self.stats['hits'] += 1
                return json.loads(value)
            self.stats['misses'] += 1
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        if not self.enabled:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, ensure_ascii=False)
            self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """删除缓存"""
        if not self.enabled or not keys:
            return 0
        try:
            return self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return 0
    
    def invalidate_pattern(self, pattern: str) -> int:
        """删除匹配的所有键"""
        if not self.enabled:
            return 0
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
        return 0
    
    def cached(self, key_prefix: str, ttl: int = None):
        """装饰器：自动缓存函数结果"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                # 生成缓存键
                cache_key = self._generate_key(key_prefix, args, kwargs)
                
                # 尝试从缓存获取
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 写入缓存
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    def _generate_key(self, prefix: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        params_str = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{prefix}:{params_hash}"
    
    def get_stats(self):
        """获取缓存统计"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        return {
            'hit_rate': f"{hit_rate:.2f}%",
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'enabled': self.enabled
        }
