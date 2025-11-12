from flask import Flask, request, jsonify
from backend.bot.bot_core import ChatBot
from backend.scraper.run_scraper import run_with_config

app = Flask(__name__)
bot = ChatBot()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "MonAgent API is running 🚀"})

@app.route("/scrape", methods=["POST"])
def scrape():
    payload = request.get_json(silent=True) or {}
    config_name = payload.get("config", "clubinject_scottsdale")
    try:
        rows, out_path, sample = run_with_config(config_name)
        return jsonify({
            "status": "success",
            "message": f"{config_name} scraper execution completed",
            "rows": rows, "output": out_path, "sample": sample
        })
    except PermissionError as e:
        return jsonify({"status": "blocked_by_robots", "message": str(e)}), 451
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Receive a message from the frontend and return ChatBot's reply"""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message = data["message"]
    response = bot.get_response(user_message)
    return jsonify({"reply": response})

if __name__ == "__main__":
    import os
    # Ensure the path is correct
    os.environ["PYTHONPATH"] = "."
    app.run(host="0.0.0.0", port=5000, debug=True)