from datetime import datetime
from models import db

class ClockIn(db.Model):
    """打卡记录模型"""
    __tablename__ = 'clock_in'
    
    id = db.Column(db.Integer, primary_key=True)
    clock_in_time = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ClockIn {self.id}: {self.clock_in_time}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'clock_in_time': self.clock_in_time.strftime('%Y-%m-%d %H:%M:%S') if self.clock_in_time else '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }
