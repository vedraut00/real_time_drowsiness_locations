#!/usr/bin/env python3
"""
Cloud Dashboard - EC2 Instance
Centralized authentication and data visualization for multiple drowsiness detection devices
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import json
import os
import hashlib
import secrets
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# In-memory storage (use database in production)
users_db = {}
devices_db = {}
alerts_db = []
device_stats = defaultdict(lambda: {
    "status": "offline",
    "last_seen": None,
    "total_alerts": 0,
    "session_start": None,
    "blinks": 0,
    "yawns": 0,
    "location": {"lat": 0, "lng": 0, "address": "Unknown"}
})

def load_users():
    """Load users from file"""
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            return json.load(f)
    return {
        "admin": {
            "password": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "admin",
            "email": "admin@example.com"
        }
    }

def save_users():
    """Save users to file"""
    with open('users.json', 'w') as f:
        json.dump(users_db, f, indent=2)

# Load users on startup
users_db = load_users()

@app.route('/')
def index():
    """Main dashboard - requires login"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    user_role = users_db.get(username, {}).get('role', 'user')
    
    return render_template('cloud_dashboard.html', 
                         username=username, 
                         role=user_role,
                         devices=devices_db)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if username in users_db:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if users_db[username]['password'] == password_hash:
                session['logged_in'] = True
                session['username'] = username
                session['role'] = users_db[username]['role']
                
                if request.is_json:
                    return jsonify({"success": True, "redirect": url_for('index')})
                return redirect(url_for('index'))
        
        error = "Invalid username or password"
        if request.is_json:
            return jsonify({"success": False, "error": error})
        return render_template('cloud_login.html', error=error)
    
    return render_template('cloud_login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if username in users_db:
            error = "Username already exists"
            if request.is_json:
                return jsonify({"success": False, "error": error})
            return render_template('cloud_register.html', error=error)
        
        # Create new user
        users_db[username] = {
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "role": "user",
            "email": email,
            "created_at": datetime.now().isoformat()
        }
        save_users()
        
        if request.is_json:
            return jsonify({"success": True, "redirect": url_for('login')})
        return redirect(url_for('login'))
    
    return render_template('cloud_register.html')

@app.route('/api/device/register', methods=['POST'])
def register_device():
    """Register a new device"""
    data = request.json
    device_id = data.get('device_id')
    device_name = data.get('device_name', f'Device-{device_id[:8]}')
    api_key = data.get('api_key')
    
    # Simple API key validation (use proper auth in production)
    if not api_key or api_key != os.environ.get('DEVICE_API_KEY', 'default_key_change_me'):
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    devices_db[device_id] = {
        "name": device_name,
        "registered_at": datetime.now().isoformat(),
        "last_seen": datetime.now().isoformat()
    }
    
    return jsonify({"success": True, "device_id": device_id})

@app.route('/api/device/heartbeat', methods=['POST'])
def device_heartbeat():
    """Device heartbeat to update status"""
    data = request.json
    device_id = data.get('device_id')
    
    if device_id not in devices_db:
        return jsonify({"success": False, "error": "Device not registered"}), 404
    
    device_stats[device_id]["status"] = "online"
    device_stats[device_id]["last_seen"] = datetime.now().isoformat()
    devices_db[device_id]["last_seen"] = datetime.now().isoformat()
    
    # Broadcast device status update
    socketio.emit('device_status', {
        'device_id': device_id,
        'status': 'online',
        'last_seen': device_stats[device_id]["last_seen"]
    })
    
    return jsonify({"success": True})

@app.route('/api/device/alert', methods=['POST'])
def receive_alert():
    """Receive alert from device"""
    data = request.json
    device_id = data.get('device_id')
    
    if device_id not in devices_db:
        return jsonify({"success": False, "error": "Device not registered"}), 404
    
    alert = {
        "id": len(alerts_db) + 1,
        "device_id": device_id,
        "device_name": devices_db[device_id].get('name', device_id),
        "timestamp": data.get('timestamp', datetime.now().isoformat()),
        "duration": data.get('duration', 0),
        "location": data.get('location', {}),
        "severity": "critical" if data.get('duration', 0) > 5 else "warning"
    }
    
    alerts_db.append(alert)
    device_stats[device_id]["total_alerts"] += 1
    
    # Broadcast alert to all connected clients
    socketio.emit('new_alert', alert)
    
    return jsonify({"success": True, "alert_id": alert["id"]})

@app.route('/api/device/stats', methods=['POST'])
def receive_stats():
    """Receive statistics from device"""
    data = request.json
    device_id = data.get('device_id')
    
    if device_id not in devices_db:
        return jsonify({"success": False, "error": "Device not registered"}), 404
    
    # Update device statistics
    stats = data.get('stats', {})
    device_stats[device_id].update({
        "blinks": stats.get('blink_count', 0),
        "yawns": stats.get('yawn_count', 0),
        "continuous_sleep": stats.get('continuous_sleep', 0),
        "fps": stats.get('fps', 0),
        "location": data.get('location', device_stats[device_id]["location"])
    })
    
    # Broadcast stats update
    socketio.emit('device_stats', {
        'device_id': device_id,
        'stats': device_stats[device_id]
    })
    
    return jsonify({"success": True})

@app.route('/api/dashboard/data')
def get_dashboard_data():
    """Get all dashboard data"""
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    # Calculate summary statistics
    total_devices = len(devices_db)
    online_devices = sum(1 for d in device_stats.values() if d["status"] == "online")
    total_alerts = len(alerts_db)
    recent_alerts = [a for a in alerts_db if 
                    datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=24)]
    
    return jsonify({
        "summary": {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": total_devices - online_devices,
            "total_alerts": total_alerts,
            "alerts_24h": len(recent_alerts)
        },
        "devices": [
            {
                "id": device_id,
                "name": device_info.get('name', device_id),
                "status": device_stats[device_id]["status"],
                "last_seen": device_stats[device_id]["last_seen"],
                "stats": device_stats[device_id]
            }
            for device_id, device_info in devices_db.items()
        ],
        "recent_alerts": sorted(alerts_db, key=lambda x: x['timestamp'], reverse=True)[:20]
    })

@app.route('/api/alerts/history')
def get_alerts_history():
    """Get alert history with filtering"""
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    device_id = request.args.get('device_id')
    hours = int(request.args.get('hours', 24))
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    filtered_alerts = [
        a for a in alerts_db
        if datetime.fromisoformat(a['timestamp']) > cutoff_time
        and (not device_id or a['device_id'] == device_id)
    ]
    
    return jsonify({
        "alerts": sorted(filtered_alerts, key=lambda x: x['timestamp'], reverse=True),
        "count": len(filtered_alerts)
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if session.get('logged_in'):
        emit('connection_response', {'status': 'connected'})
        # Send current dashboard data
        emit('dashboard_update', get_dashboard_data().json)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

@socketio.on('subscribe_device')
def handle_subscribe(data):
    """Subscribe to specific device updates"""
    device_id = data.get('device_id')
    if device_id:
        join_room(f'device_{device_id}')
        emit('subscribed', {'device_id': device_id})

@socketio.on('unsubscribe_device')
def handle_unsubscribe(data):
    """Unsubscribe from device updates"""
    device_id = data.get('device_id')
    if device_id:
        leave_room(f'device_{device_id}')
        emit('unsubscribed', {'device_id': device_id})

if __name__ == '__main__':
    print("🌐 Starting Cloud Dashboard Server...")
    print("📊 Dashboard: http://0.0.0.0:5000")
    print("🔐 Default login: admin / admin123")
    print("⚠️  Change default password in production!")
    
    # Run on all interfaces for EC2
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
