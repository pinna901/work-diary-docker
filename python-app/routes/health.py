from flask import Blueprint, jsonify
from models import db, WorkLog  # 导入 WorkLog 模型
from services.cache_service import CacheService

health_bp = Blueprint('health', __name__)
cache_service = CacheService()

@health_bp.route('/health', methods=['GET'])
def health_check():
    """容器健康检查"""
    return jsonify({'status': 'healthy'}), 200


@health_bp.route('/api/status', methods=['GET'])
def api_status():
    """详细状态检查"""
    try:
        # 测试数据库连接
        db.session.execute(db. text('SELECT 1'))
        db_status = 'connected'
        
        # 🔥 新增：查询打卡天数
        work_count = WorkLog.query.count()
    except Exception as e:
        db_status = 'disconnected'
        work_count = 0
    
    # 获取缓存统计
    cache_stats = cache_service.get_stats()
    
    return jsonify({
        'status': 'online',
        'database': db_status,
        'cache':  cache_stats,
        'count': work_count,  # 🔥 添加打卡天数
        'db': db_status       # 🔥 添加前端期望的字段
    }), 200