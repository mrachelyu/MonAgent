# # backend/api/app.py
# from flask import Flask, request, jsonify
# from backend.bot.bot_core import ChatBot

# app = Flask(__name__)
# bot = ChatBot()

# @app.route("/", methods=["GET"])
# def home():
#     return jsonify({"message": "MonAgent API is running 🚀"})

# @app.route("/chat", methods=["POST"])
# def chat():
#     """接收前端傳來的訊息，回傳 ChatBot 的回覆"""
#     data = request.get_json()
#     if not data or "message" not in data:
#         return jsonify({"error": "Missing 'message' field"}), 400

#     user_message = data["message"]
#     response = bot.get_response(user_message)
#     return jsonify({"reply": response})

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

# backend/api/app.py
from flask import Flask, request, jsonify
from backend.bot.bot_core import ChatBot
from backend.scraper.run_scraper import main as run_scraper

app = Flask(__name__)
bot = ChatBot()

@app.route("/scrape", methods=["POST"])
def scrape():
    """觸發爬蟲執行"""
    try:
        run_scraper()
        return jsonify({"status": "success", "message": "爬蟲已執行完成"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """接收前端傳來的訊息，回傳 ChatBot 的回覆"""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message = data["message"]
    response = bot.get_response(user_message)
    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)