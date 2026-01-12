from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import redis
import time
import json
import requests
import os
import logging
from logging.handlers import RotatingFileHandler
from utils import add
from groq import Groq


app = Flask(__name__)

# ================= 日志配置 =================
# 确保日志目录存在
os.makedirs('logs', exist_ok=True)

# 配置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 文件日志处理器 - 自动轮转
file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# 控制台日志处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 配置 Flask 应用日志
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.INFO)

# ================= CORS 配置 =================
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ================= 配置区域 =================
# 从环境变量中读取，读取不到则使用备用值

# 初始化 Groq 客户端
groq_api_key = os.getenv("GROQ_API_KEY")
if groq_api_key:
    try:
        groq_client = Groq(api_key=groq_api_key)
        app.logger.info('✅ Groq AI service initialized successfully')
    except Exception as e:
        app.logger.warning(f'⚠️ Failed to initialize Groq client: {e}')
        groq_client = None
else:
    app.logger.warning('⚠️ GROQ_API_KEY not set, AI polish feature will be disabled')
    groq_client = None

db_password = os.getenv('MYSQL_ROOT_PASSWORD', '0901')
db_host = os.getenv('DB_HOST', 'db')
db_name = os.getenv('MYSQL_DATABASE', 'work_diary_db')

# 2. 拼接连接字符串
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化 MySQL(MariaDB)
db = SQLAlchemy(app)

# 初始化 Redis
try:
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    # 测试连接
    r.ping()
    app.logger.info('✅ Redis connection successful')
except Exception as e:
    app.logger.error(f'❌ Redis connection failed: {e}')
    r = None

# ================= 数据库模型 =================
# 定义一张叫 diary 的表
class Diary(db.Model):
    id = db.Column(db.Integer, primary_key=True)          # ID (主键)
    content = db.Column(db.Text, nullable=False)          # 日记内容 (Text类型支持长文本)
    quote = db.Column(db.String(500))                     # 每日一句
    created_at = db.Column(db.DateTime, default=db.func.now()) # 创建时间

    # 把数据库对象变成字典，方便转 JSON
    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "quote": self.quote,
            # 把时间转成好看的字符串
            "time": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ""
        }

# ================= 初始化 (带重试机制) =================
# 这是一个死循环，直到连上数据库才会继续往下走
def wait_for_db():
    retries = 0
    max_retries = 30  # 最多试 30 次
    while retries < max_retries:
        try:
            with app.app_context():
                db.create_all()
                app.logger.info("✅ 数据库连接成功，表已就绪。")
                return True # 成功了，跳出函数
        except Exception as e:
            retries += 1
            app.logger.warning(f"⚠️ 数据库还没准备好，正在重试 ({retries}/{max_retries})... 错误: {e}")
            time.sleep(2) # 等 2 秒再试
    
    app.logger.error("❌ 错误：超过最大重试次数，数据库连接失败。")
    return False

# 执行等待逻辑
wait_for_db()

# ================= 辅助函数 =================
def get_daily_quote():
    try:
        # 设置 3 秒超时，防止卡住
        resp = requests.get("https://v1.hitokoto.cn/?c=i&c=d&encode=json", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return f"{data['hitokoto']} —— {data['from']}"
    except Exception as e:
        app.logger.warning(f"⚠️ Failed to fetch daily quote: {e}")
    return "Life was like a box of chocolate, you never know what you are gonna to get. "

# ================= 错误处理器 =================
@app.errorhandler(400)
def bad_request(e):
    app.logger.warning(f'⚠️ Bad request: {e}')
    return jsonify({"error": "Bad Request", "message": str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f'⚠️ Resource not found: {request.path}')
    return jsonify({"error": "Not Found", "message": "The requested resource was not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f'❌ Internal server error: {e}', exc_info=True)
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'❌ Unhandled Exception: {e}', exc_info=True)
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500

# ================= API 接口 =================

@app.route('/')
def hello():
    return "Work Diary Backend (MySQL + Redis) is Running!"

# 健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# 1. 状态检查 (前端用)
@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        # 测试 Redis 连接
        if r:
            count = r.get('daily_clock_in_count')
        else:
            count = 0
        
        # 测试数据库连接
        db_status = "connected"
        try:
            db.session.execute('SELECT 1')
        except:
            db_status = "disconnected"
        
        return jsonify({
            "status": "online",
            "db": "MySQL",
            "db_status": db_status,
            "count": int(count) if count else 0,
            "ai_enabled": groq_client is not None
        })
    except Exception as e:
        app.logger.error(f"❌ Status check failed: {e}")
        return jsonify({"status": "error", "count": 0}), 500

# 2. 打卡 (依然存 Redis)
@app.route('/api/clock-in', methods=['POST', 'GET'])
def clock_in():
    try:
        if not r:
            app.logger.error("❌ Redis service not available")
            return jsonify({"error": "Redis service not available"}), 503
        
        count = r.incr('daily_clock_in_count')
        app.logger.info(f"✅ Clock in success, count: {count}")
        return jsonify({
            "message": "Clock in success!", 
            "count": count
        })
    except Exception as e:
        app.logger.error(f"❌ Clock in failed: {e}")
        return jsonify({"error": str(e)}), 500

# 3. 写日记 (存 MySQL!)
@app.route('/api/diary', methods=['POST'])
def add_diary():
    try:
        # 验证请求体
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        
        content = data.get('content', '').strip()
        if not content:
            return jsonify({"error": "日记内容不能为空"}), 400
        
        quote = get_daily_quote()
        
        # 创建对象
        new_entry = Diary(content=content, quote=quote)
        
        db.session.add(new_entry) # 添加到暂存区
        db.session.commit()       # 提交到数据库
        
        app.logger.info(f"✅ Diary saved successfully, id: {new_entry.id}")
        return jsonify({
            "message": "Saved to MySQL!", 
            "entry": new_entry.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()     # 如果出错，回滚
        app.logger.error(f"❌ Failed to save diary: {e}")
        return jsonify({"error": str(e)}), 500

# 4. 看日记 (读 MySQL!)
@app.route('/api/diary', methods=['GET'])
def get_diary():
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 限制每页最大数量
        if per_page > 100:
            per_page = 100
        if page < 1:
            page = 1
        
        # 查询所有，按 ID 倒序排列 (最新的在最前)
        pagination = Diary.query.order_by(Diary.id.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "diaries": [d.to_dict() for d in pagination.items]
        })
    except Exception as e:
        app.logger.error(f"❌ Failed to fetch diaries: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai-polish', methods=['POST'])
def ai_polish():
    try:
        # 检查 AI 服务是否可用
        if not groq_client:
            app.logger.warning("⚠️ AI service not available")
            return jsonify({"error": "AI service is currently unavailable"}), 503
        
        # 验证请求体
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        
        raw_content = data.get('content', '').strip()
        if not raw_content:
            return jsonify({"error": "写点东西再让我润色嘛"}), 400

        # 调用 Llama 3.3，设置超时
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "你是一个专业的程序员日报助手。请把用户输入的简单描述，联想到一段你觉得有意义的话，语气积极向上，字数30字左右。直接输出日报内容，不要加'好的'等废话。"
                },
                {
                    "role": "user", 
                    "content": raw_content
                }
            ],
            temperature=0.7,
            max_tokens=500,
            timeout=10
        )
        
        # 获取回复
        polished_text = completion.choices[0].message.content
        app.logger.info(f"✅ AI polish success for content: {raw_content[:50]}...")
        return jsonify({"result": polished_text})

    except Exception as e:
        app.logger.error(f"❌ Groq API call failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)