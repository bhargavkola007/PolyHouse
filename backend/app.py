from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import os
from waitress import serve

# 🌿 Flask App Setup
app = Flask(__name__, static_folder='../frontend', static_url_path='/')

# ✅ Enable CORS (allow Render frontend + ESP device)
CORS(app, resources={r"/*": {"origins": ["*", "https://polyhouse-qqiy.onrender.com"]}})

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

# 🌿 IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# 🌿 Serve Frontend Files (for fallback)
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('../frontend', path)

# ✅ Health check
@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


# 🟢 POST - Receive temperature data from ESP32
@app.route('/sensors/data', methods=['POST'])
def save_temp():
    try:
        data = request.get_json(force=True)
        temperature = data.get("temperature")

        if temperature is None:
            return jsonify({"error": "Missing 'temperature' field"}), 400

        doc = {
            "temperature": float(temperature),
            "timestamp": datetime.utcnow()  # stored in UTC
        }
        temp_collection.insert_one(doc)
        print(f"🌡️ Received temperature: {temperature}")
        return jsonify({"message": "Temperature saved successfully!"}), 200

    except Exception as e:
        print("❌ Error saving temperature:", e)
        return jsonify({"error": str(e)}), 500


# 🟢 GET - Fetch all temperature records (converted to IST)
# 🟢 GET - Fetch paginated temperature records
@app.route('/sensors/data', methods=['GET'])
def get_all_data():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 10))

        skip = (page - 1) * size

        cursor = temp_collection.find({}, {"_id": 0}) \
            .sort("timestamp", -1) \
            .skip(skip) \
            .limit(size)

        result = []

        for d in cursor:
            ts = d.get("timestamp")

            if ts:
                ts = ts.replace(tzinfo=timezone.utc).astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts = "N/A"

            result.append({
                "waterTemperature": d.get("temperature"),
                "timestamp": ts
            })

        return jsonify(result), 200

    except Exception as e:
        print("❌ Error fetching data:", e)
        return jsonify({"error": str(e)}), 500

# 🟢 GET - Fetch latest temperature record (converted to IST)
@app.route('/sensors/latest', methods=['GET'])
def get_latest():
    try:
        latest = temp_collection.find_one(sort=[("timestamp", -1)])
        if not latest:
            return jsonify({"temperature": None}), 404

        ist_time = latest["timestamp"].replace(tzinfo=timezone.utc).astimezone(IST)

        return jsonify({
            "_id": str(latest["_id"]),
            "waterTemperature": latest.get("temperature"),
            "timestamp": ist_time.strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        print("❌ Error fetching latest:", e)
        return jsonify({"error": str(e)}), 500


# 🟢 POST - Control relay ON/OFF
@app.route('/sensors/control/<device>', methods=['POST'])
def control_device(device):
    try:
        data = request.get_json(force=True)
        state = data.get("state", "").upper()

        if state not in ["ON", "OFF"]:
            return jsonify({"error": "Invalid state (use ON or OFF)"}), 400

        relay_collection.update_one(
            {"device": device},
            {"$set": {"state": state, "timestamp": datetime.utcnow()}},
            upsert=True
        )

        print(f"⚡ Relay '{device}' turned {state}")
        return jsonify({"message": f"{device} turned {state}"}), 200

    except Exception as e:
        print("❌ Relay control error:", e)
        return jsonify({"error": str(e)}), 500


# 🟢 GET - Get current relay state (converted to IST)
@app.route('/sensors/control/<device>', methods=['GET'])
def get_relay_state(device):
    try:
        record = relay_collection.find_one({"device": device})
        if record:
            ist_time = record["timestamp"].replace(tzinfo=timezone.utc).astimezone(IST)
            return jsonify({
                "device": device,
                "state": record["state"],
                "timestamp": ist_time.strftime("%Y-%m-%d %H:%M:%S")
            }), 200
        else:
            # Default state is OFF
            return jsonify({"device": device, "state": "OFF"}), 200
    except Exception as e:
        print("❌ Relay state error:", e)
        return jsonify({"error": str(e)}), 500


# 🌿 Run app (Waitress for production)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Server running on port {port}")
    serve(app, host="0.0.0.0", port=port)
