import requests
import logging

logger = logging.getLogger(__name__)

class QuoteService:
    """每日一句服务"""
    
    def __init__(self, cache_service=None):
        self.cache = cache_service
        self.api_url = "https://v1.hitokoto.cn/?c=i&c=d&encode=json"
        self.default_quote = "Life was like a box of chocolate, you never know what you are gonna to get. —— Forrest Gump"
    
    def get_daily_quote(self):
        """获取每日一句（带缓存）"""
        # 尝试从缓存获取
        if self.cache:
            cached = self.cache.get('daily_quote')
            if cached:
                return cached
        
        # 调用 API
        try:
            resp = requests.get(self.api_url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                quote = f"{data['hitokoto']} —— {data['from']}"
                
                # 写入缓存（24 小时）
                if self.cache:
                    self.cache.set('daily_quote', quote, ttl=86400)
                
                return quote
        except Exception as e:
            logger.warning(f"Failed to fetch daily quote: {e}")
        
        return self.default_quote
