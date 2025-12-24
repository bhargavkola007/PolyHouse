from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.text import MIMEText
import os
from waitress import serve

BASE_URL = os.getenv("https://polyhouse-qqiy.onrender.com/sensors", "http://localhost:8080")


# ================= FLASK SETUP =================
app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

# ================= DATABASE ====================
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://polyhouse:12345@cluster0.alfrvs9.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URI)
db = client["sensors"]
temp_collection = db["temperature_data"]
relay_collection = db["relay_control"]
users_collection = db["users"]

print("✅ MongoDB Connected")

# ================= TIMEZONE ====================
IST = timezone(timedelta(hours=5, minutes=30))

# ================= EMAIL CONFIG =================
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_EMAIL = "bhargavkola53@gmail.com"

def send_email(to, subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        print("📧 Email sent")
    except Exception as e:
        print("❌ Email error:", e)

# ================= FRONTEND ====================
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('../frontend', path)

# ================= HEALTH ======================
@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

# ================= SENSOR APIs =================
@app.route('/sensors/data', methods=['POST'])
def save_temp():
    data = request.get_json(force=True)
    temperature = data.get("temperature")

    if temperature is None:
        return jsonify({"error": "Temperature missing"}), 400

    temp_collection.insert_one({
        "temperature": float(temperature),
        "timestamp": datetime.now(timezone.utc)
    })

    return jsonify({"message": "Temperature saved"}), 200

@app.route('/sensors/data', methods=['GET'])
def get_all_temp():
    data = list(temp_collection.find().sort("timestamp", -1))
    return jsonify([
        {
            "waterTemperature": d["temperature"],
            "timestamp": d["timestamp"].astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
        } for d in data
    ])

@app.route('/sensors/latest', methods=['GET'])
def latest_temp():
    d = temp_collection.find_one(sort=[("timestamp", -1)])
    if not d:
        return jsonify({"waterTemperature": None}), 404

    return jsonify({
        "waterTemperature": d["temperature"],
        "timestamp": d["timestamp"].astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
    })

# ================= RELAY APIs ==================
@app.route('/sensors/control/<device>', methods=['POST'])
def set_relay(device):
    data = request.get_json(force=True)
    state = data.get("state", "").upper()

    if state not in ["ON", "OFF"]:
        return jsonify({"error": "Invalid state"}), 400

    relay_collection.update_one(
        {"device": device},
        {"$set": {
            "state": state,
            "timestamp": datetime.now(timezone.utc)
        }},
        upsert=True
    )

    return jsonify({"message": f"{device} turned {state}"}), 200

@app.route('/sensors/control/<device>', methods=['GET'])
def get_relay(device):
    r = relay_collection.find_one({"device": device})
    if not r:
        return jsonify({"device": device, "state": "OFF"}), 200

    return jsonify({
        "device": device,
        "state": r["state"],
        "timestamp": r["timestamp"].astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
    })

# ================= AUTH ========================
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(force=True)
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all([name, email, password]):
        return jsonify({"message": "All fields required"}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"message": "Email already exists"}), 409

    created_time = datetime.now(timezone.utc)

    users_collection.insert_one({
        "name": name,
        "email": email,
        "password": password,
        "status": "PENDING",
        "createdAt": created_time
    })
    
    review_link = f"{BASE_URL}/admin/review?email={email}"

    send_email(
        ADMIN_EMAIL,
        "New User Approval Request",
        f"""
New user signup request

Name: {name}
Email: {email}
Signup Time: {created_time.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S')}

Review user (Approve / Reject):
{review_link}
"""
    )

    return jsonify({"message": "Signup successful. Await admin approval."}), 201


@app.route('/admin/review')
def review_page():
    return send_from_directory('../frontend', 'admin-review.html')

@app.route('/admin/approve')
def approve():
    email = request.args.get("email")

    users_collection.update_one(
        {"email": email},
        {"$set": {
            "status": "APPROVED",
            "approvedAt": datetime.now(timezone.utc)
        }}
    )

    send_email(email, "Account Approved", "Your account is approved.")
    return "✅ User approved"

@app.route('/admin/reject')
def reject():
    email = request.args.get("email")

    users_collection.update_one(
        {"email": email},
        {"$set": {
            "status": "REJECTED",
            "rejectedAt": datetime.now(timezone.utc)
        }}
    )

    send_email(email, "Account Rejected", "Your signup request was rejected.")
    return "❌ User rejected"


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    email, password = data.get("email"), data.get("password")

    user = users_collection.find_one({"email": email})
    if not user or user["password"] != password:
        return jsonify({"message": "Invalid credentials"}), 401

    if not user["verified"]:
        return jsonify({"verified": False, "message": "Pending approval"}), 403

    return jsonify({"verified": True, "token": "dummy-token"}), 200

# ================= RUN =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Server running on {port}")
    serve(app, host="0.0.0.0", port=port)
