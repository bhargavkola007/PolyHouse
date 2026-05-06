from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import os
from waitress import serve
from threading import Thread
import time

app = Flask(__name__, static_folder='../frontend', static_url_path='/')

CORS(app, resources={r"/*": {"origins": ["*", "https://polyhouse-qqiy.onrender.com"]}})

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://polyhouse:12345@cluster0.alfrvs9.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URI)
db = client["sensors"]
temp_collection = db["temperature_data"]
relay_collection = db["relay_control"]

IST = timezone(timedelta(hours=5, minutes=30))


# ================= FRONTEND =================
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('../frontend', path)


@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


# ================= AUTO LOOP =================
def auto_loop():
    while True:
        try:
            latest = temp_collection.find_one(sort=[("timestamp", -1)])
            if latest:
                temp = latest["temperature"]
                now = datetime.utcnow()

                relay2 = relay_collection.find_one({"device": "relay2"}) or {}
                relay3 = relay_collection.find_one({"device": "relay3"}) or {}

                if temp <= 20:
                    fan = "OFF"
                    sprinkler = "OFF"
                elif temp <= 28:
                    fan = "ON"
                    sprinkler = "OFF"
                else:
                    fan = "ON"
                    sprinkler = "ON"

                if relay2.get("mode", "AUTO") == "AUTO":
                    relay_collection.update_one(
                        {"device": "relay2"},
                        {"$set": {"state": fan, "timestamp": now}},
                        upsert=True
                    )

                if relay3.get("mode", "AUTO") == "AUTO":
                    relay_collection.update_one(
                        {"device": "relay3"},
                        {"$set": {"state": sprinkler, "timestamp": now}},
                        upsert=True
                    )

            time.sleep(60)
        except Exception as e:
            print("AUTO LOOP ERROR:", e)


# ================= SENSOR DATA =================
@app.route('/sensors/data', methods=['POST'])
def save_temp():
    try:
        data = request.get_json(force=True)
        temperature = float(data.get("temperature"))

        now = datetime.utcnow()

        temp_collection.insert_one({
            "temperature": temperature,
            "timestamp": now
        })

        return jsonify({"message": "Saved"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


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
        print("Error fetching data:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/sensors/latest', methods=['GET'])
def get_latest():
    try:
        latest = temp_collection.find_one(sort=[("timestamp", -1)])
        if not latest:
            return jsonify({"temperature": None}), 404

        ist_time = latest["timestamp"].replace(tzinfo=timezone.utc).astimezone(IST)

        return jsonify({
            "waterTemperature": latest.get("temperature"),
            "timestamp": ist_time.strftime("%Y-%m-%d %H:%M:%S")
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


# ================= RELAY =================
@app.route('/sensors/control/<device>', methods=['POST'])
def control_device(device):
    try:
        data = request.get_json(force=True)

        mode = data.get("mode", "MANUAL").upper()
        state = data.get("state")

        if mode == "MANUAL":
            if state not in ["ON", "OFF"]:
                return jsonify({"error": "State required"}), 400

        elif mode == "AUTO":
            existing = relay_collection.find_one({"device": device})
            state = existing.get("state", "OFF") if existing else "OFF"

        relay_collection.update_one(
            {"device": device},
            {"$set": {
                "state": state,
                "mode": mode,
                "timestamp": datetime.utcnow()
            }},
            upsert=True
        )

        return jsonify({"device": device, "state": state, "mode": mode}), 200

    except Exception as e:
        print("Relay error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/sensors/control/<device>', methods=['GET'])
def get_relay_state(device):
    try:
        record = relay_collection.find_one({"device": device})

        if record:
            ts = record.get("timestamp")
            if ts:
                ts = ts.replace(tzinfo=timezone.utc).astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts = "N/A"

            return jsonify({
                "device": device,
                "state": record.get("state", "OFF"),
                "mode": record.get("mode", "AUTO"),
                "timestamp": ts
            }), 200

        return jsonify({"device": device, "state": "OFF", "mode": "AUTO"}), 200

    except Exception as e:
        print("Relay error:", e)
        return jsonify({"error": str(e)}), 500


# ================= START =================
if __name__ == "__main__":
    Thread(target=auto_loop, daemon=True).start()
    port = int(os.getenv("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)