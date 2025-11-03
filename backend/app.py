from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
from waitress import serve

# 🌿 Flask App Setup
app = Flask(__name__, static_folder='../frontend', static_url_path='/')

# ✅ Enable CORS for your frontend domain only (recommended)
CORS(app, resources={r"/*": {"origins": "https://polyhouse-qqiy.onrender.com"}})

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

# 🌿 Serve Frontend Files (optional — you already host frontend separately)
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')
@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200
@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('../frontend', path)

# 🟢 POST - Receive temperature data from ESP32
@app.route('/sensors/data', methods=['POST'])
def save_temp():
    try:
        data = request.get_json()
        if not data or "temperature" not in data:
            return jsonify({"error": "Invalid data"}), 400

        doc = {
            "temperature": data["temperature"],
            "timestamp": datetime.utcnow()
        }
        temp_collection.insert_one(doc)
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

# 🟢 GET - Fetch latest temperature record
@app.route('/sensors/latest', methods=['GET'])
def get_latest():
    try:
        doc = temp_collection.find().sort("timestamp", -1).limit(1)
        latest = next(doc, None)
        if not latest:
            return jsonify({"temperature": None}), 404

        latest["_id"] = str(latest["_id"])
        latest["timestamp"] = latest["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        latest["waterTemperature"] = latest.pop("temperature", None)
        return jsonify(latest), 200
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

        print(f"Relay {device} turned {state}")
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
        else:
            return jsonify({"device": device, "state": "OFF"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🌿 Run app
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))