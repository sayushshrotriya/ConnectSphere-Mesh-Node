import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Render instance optimized secure path layout
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'connectsphere_v9.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. SOS Incidents Table Fix
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sos_feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT NOT NULL
        )
    ''')
    
    # 2. Resource Offers Table Fix
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resource_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            helper_name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            contact_details TEXT NOT NULL
        )
    ''')
    
    # 3. Global Broadcast Alerts Table Fix
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_text TEXT NOT NULL
        )
    ''')

    # 4. Missing Persons Directory Table Fix
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS missing_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            contact_info TEXT NOT NULL,
            status TEXT DEFAULT 'Missing'
        )
    ''')

    # 5. Safe Zones Table Fix
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS safe_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            capacity TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    
    # Seed data injection if dashboard directories are empty
    cursor.execute("SELECT COUNT(*) FROM safe_zones")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO safe_zones (name, address, capacity, status) VALUES (?, ?, ?, ?)
        ''', [
            ("Central Base Camp 1", "Stadium Ground, Sector 4", "500", "🟢 Operational"),
            ("Medical Relief Wing", "St. Xavier High School", "250", "🟢 Active Depot"),
            ("Emergency Shelter 3", "Old Metro Complex", "800", "🟡 Near Capacity")
        ])

    cursor.execute("SELECT COUNT(*) FROM announcements")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO announcements (alert_text) VALUES (?)", 
                       ("⚠️ ALL NODES: EMP Recovery Protocol initialized. Mesh connection established.",))
        
    conn.commit()
    conn.close()
    print("📢 All Core Tables Verified & Created Successfully!")

@app.route('/')
def home():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'index.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"<h3>Core interface source file load error. Make sure templates/index.html is uploaded on GitHub.</h3> Error: {str(e)}"

# --- API ENDPOINTS PIPELINE ---

@app.route('/api/sos', methods=['GET', 'POST'])
def handle_sos():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO sos_feed (name, location, message, category) VALUES (?, ?, ?, ?)',
                     (data['name'], data['location'], data['message'], data['category']))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    
    rows = conn.execute('SELECT * FROM sos_feed ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/offers', methods=['GET', 'POST'])
def handle_offers():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO resource_offers (helper_name, resource_type, contact_details) VALUES (?, ?, ?)',
                     (data['helper_name'], data['resource_type'], data['contact_details']))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    
    rows = conn.execute('SELECT * FROM resource_offers ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/broadcast', methods=['GET', 'POST'])
def handle_broadcast():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO announcements (alert_text) VALUES (?)', (data['alert_text'],))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    
    row = conn.execute('SELECT * FROM announcements ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"alert_text": "No alerts on current frequency spectrum."})

@app.route('/api/missing', methods=['GET', 'POST'])
def handle_missing():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO missing_persons (person_name, last_seen, contact_info) VALUES (?, ?, ?)',
                     (data['person_name'], data['last_seen'], data['contact_info']))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    
    rows = conn.execute('SELECT * FROM missing_persons ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/shelters', methods=['GET'])
def handle_shelters():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM safe_zones ORDER BY id ASC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
