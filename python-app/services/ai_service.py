from groq import Groq
import os

class AIService:
    """AI 服务封装"""
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        self.timeout = int(os.getenv('GROQ_TIMEOUT', 10))
    
    def is_available(self):
        return self.client is not None
    
    def polish_text(self, content):
        """文本润色"""
        if not self.is_available():
            raise ValueError("AI service not available")
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的程序员日报助手。请把用户输入的简单描述，联想到一段你觉得有意义的话，语气积极向上，字数30字左右。"
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                temperature=0.7,
                max_tokens=500,
                timeout=self.timeout
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"AI polish failed: {str(e)}")
