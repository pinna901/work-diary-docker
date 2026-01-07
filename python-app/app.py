from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import redis
import time
import json
import requests

app = Flask(__name__)

# ================= 配置区域 =================
# 配置 MySQL 连接
# 格式: mysql+pymysql://用户名:密码@服务名/数据库名
# 注意：密码已改为 0901
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:0901@db/work_diary_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化 MySQL
db = SQLAlchemy(app)

# 初始化 Redis (保持不变)
r = redis.Redis(host='redis', port=6379, decode_responses=True)

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
                print(">>> 数据库连接成功，表已就绪。")
                return True # 成功了，跳出函数
        except Exception as e:
            retries += 1
            print(f">>> 数据库还没准备好，正在重试 ({retries}/{max_retries})... 错误: {e}")
            time.sleep(2) # 等 2 秒再试
    
    print(">>> 错误：超过最大重试次数，数据库连接失败。")
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
    except:
        pass
    return "Life was like a box of chocolate, you never know what you are gonna to get. "

# ================= API 接口 =================

@app.route('/')
def hello():
    return "Work Diary Backend (MySQL + Redis) is Running!"

# 1. 状态检查 (前端用)
@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        count = r.get('daily_clock_in_count')
        return jsonify({
            "status": "online",
            "db": "MySQL",
            "count": int(count) if count else 0
        })
    except:
        return jsonify({"status": "error", "count": 0})

# 2. 打卡 (依然存 Redis)
@app.route('/api/clock-in', methods=['POST', 'GET'])
def clock_in():
    count = r.incr('daily_clock_in_count')
    return jsonify({
        "message": "Clock in success!", 
        "count": count
    })

# 3. 写日记 (存 MySQL!)
@app.route('/api/diary', methods=['POST'])
def add_diary():
    data = request.get_json()
    content = data.get('content', '（无内容）')
    quote = get_daily_quote()
    
    # 创建对象
    new_entry = Diary(content=content, quote=quote)
    
    try:
        db.session.add(new_entry) # 添加到暂存区
        db.session.commit()       # 提交到数据库
        return jsonify({
            "message": "Saved to MySQL!", 
            "entry": new_entry.to_dict()
        })
    except Exception as e:
        db.session.rollback()     # 如果出错，回滚
        return jsonify({"error": str(e)}), 500

# 4. 看日记 (读 MySQL!)
@app.route('/api/diary', methods=['GET'])
def get_diary():
    # 查询所有，按 ID 倒序排列 (最新的在最前)
    diaries = Diary.query.order_by(Diary.id.desc()).all()
    
    return jsonify({
        "total": len(diaries),
        "diaries": [d.to_dict() for d in diaries]
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
