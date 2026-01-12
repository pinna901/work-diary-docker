from datetime import datetime
from models import db

class Diary(db.Model):
    """日记模型"""
    __tablename__ = 'diary'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    quote = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Diary {self.id}: {self.content[:20]}...>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'quote': self.quote,
            'time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }
