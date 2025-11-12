# backend/bot/bot_core.py

class ChatBot:
    def __init__(self):
        self.default_reply = "Hi! I am MonAgent 🤖, currently under development~"

    def get_response(self, user_input: str) -> str:
        """Reply based on input (can be extended to AI or data queries)"""
        msg = user_input.lower()

        if "你好" in msg or "hi" in msg:
            return "Hello! Nice to meet you 😊"
        elif "肉毒" in msg or "botox" in msg:
            return "We offer botulinum toxin injection services. Please check the medical beauty section for pricing."
        else:
            return self.default_reply
