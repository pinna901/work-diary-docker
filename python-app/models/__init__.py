from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    with app.app_context():
        db.create_all()

# 🔥 导出所有模型（方便其他地方导入）
from models.diary import Diary
from models.clock_in import ClockIn

__all__ = ['db', 'init_db', 'Diary', 'ClockIn']