# backend/bot/bot_core.py
import re
from backend.bot.data_loader import load_business_data
from backend.bot.intent_classifier import IntentClassifier  

class ChatBot:

    def __init__(self, csv_path="backend/data/processed/clubinject_scottsdale.csv"):
        self.csv_path = csv_path
        self.data = load_business_data(csv_path)
        self.intent = IntentClassifier()

    # ------------------ Main Chat Function ------------------ #
    def chat(self, message: str) -> str:
        intent = self.intent.classify(message)

        # Address
        if intent == "address":
            return self._answer_address()

        # Phone
        if intent == "phone":
            return self._answer_phone()

        # Email
        if intent == "email":
            return self._answer_email()

        # About
        if intent == "about":
            return self._answer_about()

        # Membership
        if intent == "join":
            return self._answer_join()

        # Reviews
        if intent == "review":
            return self._answer_reviews()

        # Units price
        if intent == "unit_price":
            import re
            m = re.search(r"(\d+)", message)
            if m:
                units = int(m.group(1))
                return self._answer_unit_price(units)

        # Botox / Dysport pricing
        if intent == "pricing":
            return self._answer_service_summary()

        # Unknown → fallback
        return "I didn't quite understand your question. I can answer questions about: address, pricing, membership plans, reviews, and service summaries!"


    # ------------------ Response Builders ------------------ #

    def _answer_address(self):
        addr = self.data.get("address")
        if addr:
            return f"Our address is: {addr}"
        return "Address information is currently unavailable."

    def _answer_phone(self):
        phone = self.data.get("phone")
        if phone:
            return f"Our phone number is: {phone}"
        return "Phone information is currently unavailable."

    def _answer_email(self):
        email = self.data.get("email")
        if email:
            return f"You can email us at: {email}"
        return "Email information is currently unavailable."

    def _answer_about(self):
        about = self.data.get("about")
        if about:
            return f"About us:\n{about}"
        return "No 'About us' information found."

    def _answer_join(self):
        join = self.data.get("join_info")
        if join:
            return f"Membership plan info:\n{join}"
        return "Membership plan information is unavailable."

    def _answer_reviews(self):
        reviews = self.data.get("testimonials", [])
        if not reviews:
            return "No review information available."
        joined = "\n\n".join(reviews[:3])  # Return first three entries
        return f"Here are some customer reviews:\n{joined}"

    def _answer_unit_price(self, units):
        for s in self.data.get("services", []):
            if s["units"] == units:
                return f"The price for {units} units is: ${s['price']}"
        return f"Could not find pricing for {units} units."

    def _answer_service_summary(self):
        summary = self.data.get("pricing_summary")
        if summary:
            return f"Botox / Dysport pricing summary:\n{summary}"
        return "Botox / Dysport pricing information is unavailable."
