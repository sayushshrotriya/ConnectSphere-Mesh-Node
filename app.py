import sqlite3
import os
import tempfile
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Render ke persistent environment ke liye optimal database target path
DB_NAME = os.path.join(tempfile.gettempdir(), "connectsphere_v9.db")
print(f"==============================================\n👉 DATABASE TARGET PATH: {DB_NAME}\n==============================================")

def init_db():
    """Dono static aur dynamic core tables initialize karta hai."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. SOS Table
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

    # 2. Resource Offers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS help_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            helper_name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            contact_details TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Broadcasts Ticker Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Missing Persons Directory
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

    # 5. Safe Zones Directory
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS safe_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')

    # Default Dummy Data push for Broadcasts & Safe Zones (Visual representation)
    cursor.execute("SELECT COUNT(*) FROM broadcasts")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO broadcasts (alert_text) VALUES ('⚠️ SYSTEM NOTE: Standard offline communications running on local terminal. Keep frequencies tuned.')")
    
    cursor.execute("SELECT COUNT(*) FROM safe_zones")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO safe_zones (name, address, capacity, status) VALUES ('CAMP DELTA BASE', 'Sector 4 Stadium Grounds', 450, 'ACTIVE')")
        cursor.execute("INSERT INTO safe_zones (name, address, capacity, status) VALUES ('METRO SHELTER 2', 'Underground Station Suite', 150, 'FULL')")
        cursor.execute("INSERT INTO safe_zones (name, address, capacity, status) VALUES ('VALLEY HIGH SCHOOL', 'Sector 9 West Ridge', 300, 'ACTIVE')")

    conn.commit()
    conn.close()
    print("📢 All Core Tables Verified & Created Successfully!")

init_db()

# --- WEB USER ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

# 1. SOS TRANSMISSION PIPELINE
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
    return jsonify({"success": True, "message": "SOS Signal Transmitted!"}), 201

@app.route('/api/feed', methods=['GET'])
def get_feed():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, location, category, message, status, timestamp FROM sos_requests ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    feed = [{"name": r[0], "location": r[1], "category": r[2], "message": r[3], "status": r[4], "timestamp": r[5]} for r in rows]
    return jsonify(feed)

# 2. SUPPLY ALLOCATION PIPELINE
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
        return jsonify({"success": True, "message": "Supply resource logged!"}), 201
    else:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT helper_name, resource_type, contact_details, timestamp FROM help_offers ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        offers = [{"helper_name": r[0], "resource_type": r[1], "contact_details": r[2], "timestamp": r[3]} for r in rows]
        return jsonify(offers)

# 3. DIRECTORY NEWS BROADCASTS
@app.route('/api/broadcast', methods=['GET', 'POST'])
def handle_broadcast():
    if request.method == 'POST':
        data = request.get_json()
        text = data.get('alert_text')
        if not text:
            return jsonify({"error": "Text empty"}), 400
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO broadcasts (alert_text) VALUES (?)", (text,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    else:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT alert_text FROM broadcasts ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return jsonify({"alert_text": row[0] if row else "All local base networks quiet."})

# 4. MISSING BULLETINS
@app.route('/api/missing', methods=['GET', 'POST'])
def handle_missing():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('person_name')
        seen = data.get('last_seen')
        contact = data.get('contact_info')

        if not name or not seen or not contact:
            return jsonify({"error": "Missing params"}), 400

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO missing_persons (person_name, last_seen, contact_info) VALUES (?, ?, ?)",
            (name, seen, contact)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    else:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT person_name, last_seen, contact_info, status FROM missing_persons ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([{"person_name": r[0], "last_seen": r[1], "contact_info": r[2], "status": r[3]} for r in rows])

# 5. SAFE ZONES INVENTORY
@app.route('/api/shelters', methods=['GET'])
def get_shelters():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, address, capacity, status FROM safe_zones")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"name": r[0], "address": r[1], "capacity": r[2], "status": r[3]} for r in rows])

# --- SYSTEM DEPLOYMENT SERVER CONFIGURATION ---

if __name__ == '__main__':
    # Render ke automatic host binding port ko target karega
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
```
eof

### 🛠️ Isko GitHub Par Kaise Fix Karein?
1. GitHub par jao, apni repository kholo aur **`app.py`** par click karo.
2. Upper right corner me **"Pencil" (Edit)** button par click karo.
3. Purana saara code delete karke upar diya gaya **Updated Base App code** paste kar do.
4. Niche **"Commit changes"** (green button) par click karke save kar do!

### 💡 Iske Baad Kya Hoga?
Jaise hi tum commit karoge, **Render automatically is code ko dekh kar redeploy karna shuru kar dega**. Is baar use dynamic host `0.0.0.0` aur dynamic `PORT` dono mil jayenge, aur deployment full screen success ho jayegi bina scan errors ke.

Isse replace karo bhai, aur Render logs ko ek baar aur refresh hote hue dekho! 🚀🔥🏆
