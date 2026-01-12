from repositories.base_repository import BaseRepository
from models.diary import Diary
from sqlalchemy import desc

class DiaryRepository(BaseRepository):
    """日记仓储"""
    
    def __init__(self):
        super().__init__(Diary)
    
    def find_recent(self, limit=20):
        """查询最近的日记"""
        return self.model.query.order_by(desc(Diary.created_at)).limit(limit).all()
    
    def find_paginated(self, page=1, per_page=20):
        """分页查询"""
        return self.model.query.order_by(desc(Diary.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
