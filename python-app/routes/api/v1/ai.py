from flask import request, jsonify
from routes.api.v1 import api_v1_bp
from services.ai_service import AIService

ai_service = AIService()

@api_v1_bp.route('/ai/polish', methods=['POST'])
def ai_polish():
    """AI 文本润色"""
    if not ai_service.is_available():
        return jsonify({
            'error': 'AI service unavailable',
            'message': 'GROQ_API_KEY not configured'
        }), 503
    
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'error': '写点东西再让我润色嘛'}), 400
    
    try:
        result = ai_service.polish_text(data['content'])
        return jsonify({'result': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
