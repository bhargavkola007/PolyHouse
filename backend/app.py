from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from waitress import serve
import os

# 🌿 Flask App Setup (no static folder)
app = Flask(__name__)

# ✅ Allow both ESP8266 and frontend domain to access backend
CORS(app, resources={r"/*": {"origins": ["https://polyhouse-qqiy.onrender.com", "*"]}})

# 🌿 MongoDB Connection
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://polyhouse:12345@cluster0.alfrvs9.mongodb.net/?appName=Cluster0"
)

try:
    client = MongoClient(MONGO_URI)
    db = client["sensors"]
    temp_collection = db["temperature_data"]
    relay_collection = db["relay_control"]
    print("✅ MongoDB Connected Successfully")
except Exception as e:
    print("❌ MongoDB Connection Error:", e)

# 🌿 Health check
@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

# 🟢 POST - Receive temperature data from ESP8266
@app.route('/sensors/data', methods=['POST'])
def save_temp():
    try:
        data = request.get_json()
        if not data or "temperature" not in data:
            return jsonify({"error": "Invalid data"}), 400

        temp_collection.insert_one({
            "temperature": data["temperature"],
            "timestamp": datetime.utcnow()
        })
        print(f"✅ Temperature received: {data['temperature']} °C")
        return jsonify({"message": "Temperature saved successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🟢 GET - Fetch all temperature records
@app.route('/sensors/data', methods=['GET'])
def get_all_data():
    try:
        data = list(temp_collection.find().sort("timestamp", -1))
        formatted = [
            {
                "_id": str(d["_id"]),
                "waterTemperature": d.get("temperature"),
                "timestamp": d["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            }
            for d in data
        ]
        return jsonify(formatted), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🟢 GET - Fetch latest temperature
@app.route('/sensors/latest', methods=['GET'])
def get_latest():
    try:
        latest = temp_collection.find_one(sort=[("timestamp", -1)])
        if not latest:
            return jsonify({"temperature": None}), 404

        return jsonify({
            "_id": str(latest["_id"]),
            "waterTemperature": latest["temperature"],
            "timestamp": latest["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🟢 POST - Control relay ON/OFF
@app.route('/sensors/control/<device>', methods=['POST'])
def control_device(device):
    try:
        data = request.get_json()
        state = data.get("state", "").upper()
        if state not in ["ON", "OFF"]:
            return jsonify({"error": "Invalid state"}), 400

        relay_collection.update_one(
            {"device": device},
            {"$set": {"state": state, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        print(f"🔧 Relay {device} -> {state}")
        return jsonify({"message": f"{device} turned {state}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🟢 GET - Get current relay state
@app.route('/sensors/control/<device>', methods=['GET'])
def get_relay_state(device):
    try:
        record = relay_collection.find_one({"device": device})
        if record:
            return jsonify({
                "device": device,
                "state": record["state"],
                "timestamp": record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            }), 200
        return jsonify({"device": device, "state": "OFF"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🌿 Run app on Render / localhost
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
