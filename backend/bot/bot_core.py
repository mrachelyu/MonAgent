# backend/bot/bot_core.py

class ChatBot:
    def __init__(self):
        self.default_reply = "嗨！我是 MonAgent 🤖，目前我正在開發中～"

    def get_response(self, user_input: str) -> str:
        """根據輸入回覆內容（可擴充為 AI 或資料查詢）"""
        msg = user_input.lower()

        if "你好" in msg or "hi" in msg:
            return "你好！很高興見到你 😊"
        elif "肉毒" in msg or "botox" in msg:
            return "我們提供肉毒桿菌注射服務，價格請見醫美專區。"
        else:
            return self.default_reply
