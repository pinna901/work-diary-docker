from flask import Blueprint, jsonify
from models import db, ClockIn  # 🔥 直接从 models 导入
from services. cache_service import CacheService

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
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
        
        # 🔥 查询打卡次数
        clock_count = ClockIn.query.count()
    except Exception as e: 
        db_status = 'disconnected'
        clock_count = 0
    
    # 获取缓存统计
    cache_stats = cache_service.get_stats()
    
    return jsonify({
        'status': 'online',
        'database': db_status,
        'cache': cache_stats,
        'count': clock_count,  # 打卡次数
        'db': db_status        # 数据库状态
    }), 200