from repositories.clock_in_repository import ClockInRepository
from models.clock_in import ClockIn
import redis

class ClockInService:
    """打卡业务逻辑"""
    
    def __init__(self, repository=None, redis_client=None):
        self.repository = repository or ClockInRepository()
        self.redis_client = redis_client
    
    def create_clock_in(self):
        """创建新的打卡记录（保存到 MySQL 并更新 Redis 计数器）"""
        # 1. 保存到 MySQL
        clock_in = ClockIn()
        saved_clock_in = self.repository.save(clock_in)
        
        # 2. 更新 Redis 计数器
        count = 0
        if self.redis_client:
            try:
                count = self.redis_client.incr('daily_clock_in_count')
            except Exception as e:
                # Redis 失败不影响主流程，记录日志即可
                print(f"Redis error: {e}")
                count = self.repository.count_total()
        else:
            # 如果没有 Redis，从数据库统计
            count = self.repository.count_total()
        
        return saved_clock_in, count
    
    def get_clock_in_history(self, page=1, per_page=20):
        """获取打卡历史（分页）"""
        # 限制每页最大条数
        if per_page > 100:
            per_page = 100
        
        # 从数据库查询
        pagination = self.repository.find_paginated(page, per_page)
        result = {
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'records': [record.to_dict() for record in pagination.items]
        }
        
        return result
    
    def get_clock_in_stats(self):
        """获取打卡统计信息"""
        total_count = self.repository.count_total()
        return {
            'total_count': total_count
        }
