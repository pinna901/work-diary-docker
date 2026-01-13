from marshmallow import Schema, fields

class ClockInResponseSchema(Schema):
    """打卡记录响应格式"""
    id = fields.Int()
    clock_in_time = fields.Str()
    created_at = fields.Str()
