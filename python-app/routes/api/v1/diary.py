from flask import request, jsonify
from routes.api.v1 import api_v1_bp
from services.diary_service import DiaryService

diary_service = DiaryService()

@api_v1_bp.route('/diaries', methods=['POST'])
def create_diary():
    """创建日记"""
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


@api_v1_bp.route('/diaries', methods=['GET'])
def list_diaries():
    """查询日记列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # 限制最大 100
    
    try:
        result = diary_service.get_diary_list(page, per_page)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_v1_bp.route('/diaries/<int:diary_id>', methods=['GET'])
def get_diary(diary_id):
    """获取单条日记"""
    diary = diary_service.get_diary_by_id(diary_id)
    if not diary:
        return jsonify({'error': 'Diary not found'}), 404
    return jsonify(diary.to_dict()), 200
