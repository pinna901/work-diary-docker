from marshmallow import Schema, fields, validate

class DiaryCreateSchema(Schema):
    """创建日记的输入验证"""
    content = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=10000),
        error_messages={'required': '日记内容不能为空'}
    )

class DiaryResponseSchema(Schema):
    """日记响应格式"""
    id = fields.Int()
    content = fields.Str()
    quote = fields.Str()
    time = fields.Str()
