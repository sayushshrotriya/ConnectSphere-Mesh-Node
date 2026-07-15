import sqlite3
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Workspace calculation local directory ke liye
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "connectsphere_v9.db")

print("==============================================")
print(f"👉 DATABASE TARGET PATH: {DB_NAME}")
print("==============================================")

def init_db():
    """Initializes tables inside high-speed local database instance."""
    # Force open file generation on runtime initiation
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. SOS Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sos_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Help Offers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS help_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            helper_name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            contact_details TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Shelter Directory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS safe_shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            status TEXT DEFAULT 'Open'
        )
    ''')
    
    # Seeding (Pre-filling data): Check karo agar table khali hai, toh default shelters daal do
    cursor.execute("SELECT COUNT(*) FROM safe_shelters")
    if cursor.fetchone()[0] == 0:
        shelters = [
            ("Central High School", "Sector 4, Main Road", 500),
            ("City Hospital Bunker", "Medical District", 150),
            ("Community Hall Alpha", "Sector 9, East Wing", 300)
        ]
        cursor.executemany("INSERT INTO safe_shelters (name, address, capacity) VALUES (?, ?, ?)", shelters)

    # 4. Missing Persons Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS missing_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            contact_info TEXT NOT NULL,
            status TEXT DEFAULT 'Missing',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Broadcast Alerts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS broadcast_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("📢 All Core Tables Verified & Created Successfully!")

# Immediate execution on import
init_db()

# --- ROUTES SYSTEM ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/sos', methods=['POST'])
def create_sos():
    data = request.get_json()
    name = data.get('name')
    location = data.get('location')
    category = data.get('category')
    message = data.get('message')

    if not name or not location or not category or not message:
        return jsonify({"error": "Missing fields"}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sos_requests (name, location, category, message) VALUES (?, ?, ?, ?)",
        (name, location, category, message)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 201

@app.route('/api/feed', methods=['GET'])
def get_feed():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, location, category, message, status, timestamp FROM sos_requests ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    feed = [{"name": r[0], "location": r[1], "category": r[2], "message": r[3], "status": r[4], "timestamp": r[5]} for r in rows]
    return jsonify(feed)

@app.route('/api/offers', methods=['GET', 'POST'])
def handle_offers():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('helper_name')
        resource = data.get('resource_type')
        contact = data.get('contact_details')

        if not name or not resource or not contact:
            return jsonify({"error": "Fields missing"}), 400

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO help_offers (helper_name, resource_type, contact_details) VALUES (?, ?, ?)",
            (name, resource, contact)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    else:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT helper_name, resource_type, contact_details, timestamp FROM help_offers ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        offers = [{"helper_name": r[0], "resource_type": r[1], "contact_details": r[2], "timestamp": r[3]} for r in rows]
        return jsonify(offers)

@app.route('/api/shelters', methods=['GET'])
def get_shelters():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, address, capacity, status FROM safe_shelters")
    rows = cursor.fetchall()
    conn.close()
    shelters = [{"name": r[0], "address": r[1], "capacity": r[2], "status": r[3]} for r in rows]
    return jsonify(shelters)

@app.route('/api/missing', methods=['GET', 'POST'])
def handle_missing():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('person_name')
        last_seen = data.get('last_seen')
        contact = data.get('contact_info')

        if not name or not last_seen or not contact:
            return jsonify({"error": "Missing input data"}), 400

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO missing_persons (person_name, last_seen, contact_info) VALUES (?, ?, ?)",
            (name, last_seen, contact)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    else:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT person_name, last_seen, contact_info, status FROM missing_persons ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        persons = [{"person_name": r[0], "last_seen": r[1], "contact_info": r[2], "status": r[3]} for r in rows]
        return jsonify(persons)

@app.route('/api/broadcast', methods=['GET', 'POST'])
def handle_broadcast():
    if request.method == 'POST':
        data = request.get_json()
        text = data.get('alert_text')
        if not text:
            return jsonify({"error": "Alert text cannot be empty"}), 400

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO broadcast_alerts (alert_text) VALUES (?)", (text,))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    else:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT alert_text FROM broadcast_alerts ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        alert = {"alert_text": row[0]} if row else {"alert_text": "No active emergency broadcasts at this moment."}
        return jsonify(alert)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)