from flask import Flask, jsonify, request
from flask_cors import CORS
from config import config
from models import db, init_db
from routes.api.v1 import api_v1_bp
from routes.health import health_bp
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from sqlalchemy import text  # 👈 新增引入，用于测试连接

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
    
    # 🔥 核心修改：数据库初始化逻辑
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
    
    # 🔥 关键修改 1：db.init_app 必须在循环外面执行！
    # 否则重试时会报错 "SQLAlchemy instance has already been registered"
    db.init_app(app)
    
    # 检测测试环境
    is_testing = app.config.get('TESTING') or os.getenv('TESTING') == 'true'
    
    if is_testing:
        try:
            with app.app_context():
                db.create_all()
                app.logger.info("✅ Test database connected (in-memory)")
                return True
        except Exception as e:
            app.logger.warning(f"⚠️ Test database init failed: {e}")
            return False
    
    # 生产环境：重试逻辑
    retries = 0
    max_retries = 30
    retry_interval = 2
    
    with app.app_context():
        while retries < max_retries: 
            try:
                # 🔥 关键修改 2：先尝试连接，确保数据库服务已就绪
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                # 连接成功后，再尝试创建表
                # 如果表已存在，create_all 通常会忽略，但为了保险起见捕获异常
                try:
                    db.create_all()
                except Exception as create_e:
                    # 如果只是表已存在的错误，我们可以忽略它
                    if "already exists" in str(create_e):
                        app.logger.info("Tables already exist, skipping creation.")
                    else:
                        raise create_e

                app.logger.info("✅ Database connected and initialized")
                return True
                
            except Exception as e: 
                retries += 1
                app.logger.warning(f"⏳ Waiting for database ({retries}/{max_retries})... Error: {str(e)}")
                time.sleep(retry_interval)
    
    app.logger.error("❌ Failed to connect to database after multiple retries")
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
    from services.clock_in_service import ClockInService
    import redis
    
    # 注意：这里实例化服务可能会依赖数据库连接
    # 建议在具体路由函数内部实例化，或者确保数据库已连接
    diary_service = DiaryService()
    ai_service = AIService()
    
    # Redis 连接
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        r.ping()
    except:
        r = None
    
    # 初始化 ClockInService
    clock_in_service = ClockInService(redis_client=r)
    
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
        try:
            saved_record, count = clock_in_service.create_clock_in()
            return jsonify({'message': 'Clock in success!', 'count': count})
        except Exception as e:
            app.logger.error(f'Clock in error: {e}')
            return jsonify({'error': str(e)}), 500
    
    # 新增：打卡历史查询接口
    @app.route('/api/clock-in/history', methods=['GET'])
    def get_clock_in_history():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        try:
            result = clock_in_service.get_clock_in_history(page, per_page)
            return jsonify(result), 200
        except Exception as e:
            app.logger.error(f'Get clock-in history error: {e}')
            return jsonify({'error': str(e)}), 500
    
    # 兼容旧的 /api/diary
    @app.route('/api/diary', methods=['POST'])
    def add_diary_legacy():
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


# 为 Gunicorn 和直接运行提供 app 对象
if __name__ == '__main__': 
    # 直接使用 python app.py 运行
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    # 使用 Gunicorn 运行
    app = create_app()