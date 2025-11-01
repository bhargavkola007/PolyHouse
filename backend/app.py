
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 🔗 MongoDB Connection
MONGO_URI = "mongodb+srv://polyhouse:12345@cluster0.alfrvs9.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["sensors"]
temp_collection = db["temperature_data"]
relay_collection = db["relay_control"]

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


# 🟢 GET - Fetch all temperature records (for web dashboard)
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


# 🟢 Root route
@app.route('/')
def home():
    return jsonify({"message": "Polyhouse Temperature Monitoring API is running"}), 200


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8080, debug=True)
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
