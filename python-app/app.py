from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from models import db, init_db
from routes.api.v1 import api_v1_bp
from routes.health import health_bp
import os
import logging
from logging.handlers import RotatingFileHandler
import time

def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 1. 加载配置
    config_name = config_name or os.getenv('FLASK_ENV', 'production')
    app.config.from_object(config[config_name])
    
    # 2. 配置日志
    setup_logging(app)
    
    # 3. 初始化扩展
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    init_db_with_retry(app)
    
    # 4. 注册蓝图
    app.register_blueprint(api_v1_bp)
    app.register_blueprint(health_bp)
    
    # 5. 注册错误处理
    register_error_handlers(app)
    
    # 6. 注册兼容路由（保持向后兼容）
    register_legacy_routes(app)
    
    app.logger.info('🚀 Work Diary Application Started')
    
    return app


def setup_logging(app):
    """配置日志"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)


def init_db_with_retry(app):
    """初始化数据库（带重试）"""
    retries = 0
    max_retries = 30
    
    while retries < max_retries:
        try:
            with app.app_context():
                db.init_app(app)
                db.create_all()
                app.logger.info("✅ Database connected")
                return True
        except Exception as e:
            retries += 1
            app.logger.warning(f"⏳ Waiting for database ({retries}/{max_retries})... Error: {e}")
            time.sleep(2)
    
    app.logger.error("❌ Failed to connect to database")
    return False


def register_error_handlers(app):
    """注册错误处理器"""
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f'Internal Server Error: {e}')
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f'Unhandled Exception: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


def register_legacy_routes(app):
    """注册兼容路由（保持向后兼容）"""
    from services.diary_service import DiaryService
    from services.ai_service import AIService
    import redis
    
    diary_service = DiaryService()
    ai_service = AIService()
    
    # Redis 连接
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        r.ping()
    except:
        r = None
    
    @app.route('/')
    def hello():
        return jsonify({
            'service': 'Work Diary Backend',
            'status': 'running',
            'api_version': 'v1'
        })
    
    # 兼容旧的 /api/clock-in
    @app.route('/api/clock-in', methods=['POST', 'GET'])
    def clock_in():
        if not r:
            return jsonify({'error': 'Redis service unavailable'}), 503
        try:
            count = r.incr('daily_clock_in_count')
            return jsonify({'message': 'Clock in success!', 'count': count})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # 兼容旧的 /api/diary
    @app.route('/api/diary', methods=['POST'])
    def add_diary_legacy():
        from flask import request
        data = request.get_json()
        if not data or not data.get('content'):
            return jsonify({'error': '日记内容不能为空'}), 400
        try:
            diary = diary_service.create_diary(data['content'])
            return jsonify({
                'message': 'Saved to MySQL!',
                'entry': diary.to_dict()
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/diary', methods=['GET'])
    def get_diary_legacy():
        from flask import request
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        try:
            result = diary_service.get_diary_list(page, per_page)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # 兼容旧的 /api/ai-polish
    @app.route('/api/ai-polish', methods=['POST'])
    def ai_polish_legacy():
        from flask import request
        if not ai_service.is_available():
            return jsonify({'error': 'AI service unavailable'}), 503
        data = request.get_json()
        if not data or not data.get('content'):
            return jsonify({'error': '写点东西再让我润色嘛'}), 400
        try:
            result = ai_service.polish_text(data['content'])
            return jsonify({'result': result}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)