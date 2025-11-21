import re

class IntentClassifier:

    def classify(self, message: str) -> str:
        msg = message.lower().strip()

        # Address
        if any(k in msg for k in ["address", "在哪", "location", "where"]):
            return "address"

        # Phone
        if any(k in msg for k in ["phone", "電話"]):
            return "phone"

        # Email
        if "email" in msg or "mail" in msg:
            return "email"

        # About Us
        if any(k in msg for k in ["about", "你們是誰", "介紹", "who are you"]):
            return "about"

        # Membership
        if any(k in msg for k in ["member", "membership", "加入", "會員"]):
            return "join"

        # Reviews
        if any(k in msg for k in ["review", "評論", "評價"]):
            return "review"

        # Units price
        unit_match = re.search(r"(\d+)\s*units?", msg)
        if unit_match:
            return "unit_price"

        # General pricing (botox/dysport)
        if any(k in msg for k in ["botox", "dysport", "價格", "price"]):
            return "pricing"

        return "unknown"
