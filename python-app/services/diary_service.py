from repositories.diary_repository import DiaryRepository
from services.cache_service import CacheService
from services.quote_service import QuoteService
from models.diary import Diary

class DiaryService:
    """日记业务逻辑"""
    
    def __init__(self, repository=None, cache=None, quote_service=None):
        self.repository = repository or DiaryRepository()
        self.cache = cache or CacheService()
        self.quote_service = quote_service or QuoteService(cache)
    
    def create_diary(self, content):
        """创建日记"""
        # 获取每日一句
        quote = self.quote_service.get_daily_quote()
        
        # 创建日记
        diary = Diary(content=content, quote=quote)
        saved_diary = self.repository.save(diary)
        
        # 清除列表缓存
        self.cache.invalidate_pattern('diary_list:*')
        
        return saved_diary
    
    def get_diary_list(self, page=1, per_page=20):
        """获取日记列表（带缓存）"""
        cache_key = f'diary_list:page:{page}:size:{per_page}'
        
        # 尝试从缓存获取
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # 从数据库查询
        pagination = self.repository.find_paginated(page, per_page)
        result = {
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'diaries': [d.to_dict() for d in pagination.items]
        }
        
        # 写入缓存
        self.cache.set(cache_key, result, ttl=300)
        
        return result
    
    def get_diary_by_id(self, diary_id):
        """获取单条日记"""
        return self.repository.find_by_id(diary_id)
