from repositories.base_repository import BaseRepository
from models.clock_in import ClockIn
from sqlalchemy import desc

class ClockInRepository(BaseRepository):
    """打卡记录仓储"""
    
    def __init__(self):
        super().__init__(ClockIn)
    
    def find_recent(self, limit=20):
        """查询最近的打卡记录"""
        return self.model.query.order_by(desc(ClockIn.clock_in_time)).limit(limit).all()
    
    def find_paginated(self, page=1, per_page=20):
        """分页查询打卡记录"""
        return self.model.query.order_by(desc(ClockIn.clock_in_time)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    def find_by_date_range(self, start_date, end_date):
        """按日期范围查询打卡记录"""
        return self.model.query.filter(
            ClockIn.clock_in_time.between(start_date, end_date)
        ).order_by(desc(ClockIn.clock_in_time)).all()
    
    def count_total(self):
        """统计总打卡次数"""
        return self.count()
