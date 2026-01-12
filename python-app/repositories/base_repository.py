from models import db

class BaseRepository:
    """基础仓储（通用 CRUD）"""
    
    def __init__(self, model):
        self.model = model
    
    def find_by_id(self, id):
        return self.model.query.get(id)
    
    def find_all(self):
        return self.model.query.all()
    
    def save(self, entity):
        db.session.add(entity)
        db.session.commit()
        return entity
    
    def delete(self, entity):
        db.session.delete(entity)
        db.session.commit()
    
    def count(self):
        return self.model.query.count()
