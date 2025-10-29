#!/usr/bin/env python3
"""
Hybrid Drowsiness Detection System
- PC Mode: High performance OpenCV window + Web dashboard
- Web Mode: Browser-based detection
"""

import cv2
import threading
import time
import json
import os
import requests
from datetime import datetime
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
from DrowsinessDetector_Universal import TelegramBot
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_socketio import SocketIO
import winsound

# Import cloud client
try:
    from local_client import CloudClient, load_cloud_config
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False
    print("⚠️  Cloud client not available")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'drowsiness_detection_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

class HybridDrowsinessDetector:
    def __init__(self):
        self.mode = "pc"  # "pc" or "web"
        self.detection_active = False
        self.camera = None
        self.telegram_bot = None
        self.config = self.load_config()
        self.current_location = {"lat": 0, "lng": 0, "address": "Unknown"}
        
        # Statistics
        self.stats = {
            "total_alerts": 0,
            "session_alerts": 0,
            "last_alert": None,
            "session_start": datetime.now(),
            "blink_count": 0,
            "yawn_count": 0,
            "continuous_sleep": 0.0,
            "fps": 0,
            "frames_processed": 0
        }
        
        # Detection variables
        self.eyes_closed_frames = 0
        self.yawn_frames = 0
        self.continuous_sleep_time = 0.0
        
        # Initialize models and bot
        self.setup_models()
        self.setup_telegram_bot()
        self.setup_cloud_client()
        
    def load_config(self):
        """Load configuration from file"""
        config_file = 'telegram_config.json'
        default_config = {
            "bot_token": "",
            "chat_ids": [],
            "emergency_threshold": 3.0,
            "max_alerts_per_5min": 5,
            "admin_password": "admin123"
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                pass
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        with open('telegram_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_models(self):
        """Initialize detection models"""
        try:
            self.mp_face_mesh = mp.solutions.face_mesh
            print("✅ MediaPipe Face Mesh loaded")
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
    
    def setup_telegram_bot(self):
        """Setup Telegram bot"""
        if self.config.get('bot_token') and self.config.get('chat_ids'):
            self.telegram_bot = TelegramBot(
                self.config['bot_token'],
                self.config['chat_ids'],
                self.config.get('max_alerts_per_5min', 5)
            )
            print("✅ Telegram bot configured")
        else:
            print("⚠️ Telegram bot not configured")
    
    def setup_cloud_client(self):
        """Setup cloud client"""
        self.cloud_client = None
        if CLOUD_AVAILABLE:
            cloud_config = load_cloud_config()
            if cloud_config.get('enabled'):
                try:
                    self.cloud_client = CloudClient(
                        cloud_url=cloud_config['cloud_url'],
                        api_key=cloud_config['api_key'],
                        device_name=cloud_config.get('device_name')
                    )
                    print("✅ Cloud client connected")
                except Exception as e:
                    print(f"⚠️  Cloud client error: {e}")
    
    def get_current_location(self):
        """Get current location"""
        try:
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    self.current_location = {
                        "lat": data.get('lat', 0),
                        "lng": data.get('lon', 0),
                        "address": f"{data.get('city', 'Unknown')}, {data.get('regionName', 'Unknown')}, {data.get('country', 'Unknown')}"
                    }
        except Exception as e:
            print(f"❌ Location fetch failed: {e}")
        
        return self.current_location
    
    def calculate_ear(self, landmarks):
        """Calculate Eye Aspect Ratio"""
        try:
            # Left eye landmarks
            left_eye = [33, 160, 158, 133, 153, 144]
            # Right eye landmarks
            right_eye = [362, 385, 387, 263, 373, 380]
            
            def get_ear(eye_points):
                coords = []
                for i in eye_points:
                    lm = landmarks.landmark[i]
                    coords.append([lm.x, lm.y])
                coords = np.array(coords)
                
                # Vertical distances
                v1 = np.linalg.norm(coords[1] - coords[5])
                v2 = np.linalg.norm(coords[2] - coords[4])
                
                # Horizontal distance
                h = np.linalg.norm(coords[0] - coords[3])
                
                if h > 0:
                    return (v1 + v2) / (2.0 * h)
                return 0.3
            
            left_ear = get_ear(left_eye)
            right_ear = get_ear(right_eye)
            
            return (left_ear + right_ear) / 2.0
            
        except Exception as e:
            return 0.3
    
    def calculate_mar(self, landmarks):
        """Calculate Mouth Aspect Ratio"""
        try:
            # Mouth landmarks
            mouth_points = [13, 14, 269, 270, 267, 271, 272, 17]
            
            coords = []
            for i in mouth_points:
                lm = landmarks.landmark[i]
                coords.append([lm.x, lm.y])
            coords = np.array(coords)
            
            # Vertical distance
            v1 = np.linalg.norm(coords[1] - coords[7])
            
            # Horizontal distance
            h = np.linalg.norm(coords[0] - coords[4])
            
            if h > 0:
                return v1 / h
            return 0.0
            
        except Exception as e:
            return 0.0
    
    def handle_drowsiness_alert(self, duration):
        """Handle drowsiness alert"""
        location = self.get_current_location()
        timestamp = datetime.now()
        
        alert_data = {
            "timestamp": timestamp.isoformat(),
            "duration": round(duration, 1),
            "location": location,
            "alert_id": int(time.time())
        }
        
        # Update statistics
        self.stats["total_alerts"] += 1
        self.stats["session_alerts"] += 1
        self.stats["last_alert"] = timestamp.isoformat()
        
        # Send Telegram alert
        if self.telegram_bot:
            success = self.telegram_bot.send_emergency_alert(duration)
            alert_data["telegram_sent"] = success
        
        # Send to cloud dashboard
        if self.cloud_client:
            try:
                self.cloud_client.send_alert(duration, location)
            except Exception as e:
                print(f"⚠️  Cloud alert error: {e}")
        
        # Emit to web clients
        socketio.emit('drowsiness_alert', alert_data)
        
        print(f"🚨 Drowsiness alert: {duration:.1f}s at {location['address']}")
    
    def start_pc_mode(self):
        """Start PC mode with OpenCV window"""
        self.mode = "pc"
        self.detection_active = True
        self.stats["session_start"] = datetime.now()
        
        # Start detection thread
        detection_thread = threading.Thread(target=self.pc_detection_loop)
        detection_thread.daemon = True
        detection_thread.start()
        
        print("🚀 PC Mode started - OpenCV window + Web dashboard")
        return True
    
    def start_web_mode(self):
        """Start web mode (browser only)"""
        self.mode = "web"
        self.detection_active = True
        self.stats["session_start"] = datetime.now()
        
        # Start detection thread
        detection_thread = threading.Thread(target=self.web_detection_loop)
        detection_thread.daemon = True
        detection_thread.start()
        
        print("🌐 Web Mode started - Browser detection")
        return True
    
    def pc_detection_loop(self):
        """High performance PC detection with OpenCV window"""
        print("🎥 PC Detection loop started - High Performance Mode")
        
        # Initialize camera
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        # Initialize MediaPipe
        face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # FPS tracking
        fps_counter = 0
        fps_start_time = time.time()
        
        try:
            while self.detection_active and self.camera:
                ret, frame = self.camera.read()
                if not ret:
                    continue
                
                # FPS calculation
                fps_counter += 1
                if fps_counter % 30 == 0:
                    current_time = time.time()
                    current_fps = 30 / (current_time - fps_start_time)
                    fps_start_time = current_time
                    self.stats["fps"] = round(current_fps, 1)
                
                self.stats["frames_processed"] += 1
                
                # Detection
                drowsy = False
                blink_detected = False
                yawn_detected = False
                
                # Face detection
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(image_rgb)
                
                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    
                    # Calculate EAR and MAR
                    ear = self.calculate_ear(face_landmarks)
                    mar = self.calculate_mar(face_landmarks)
                    
                    # Eye closure detection
                    if ear < 0.25:
                        self.eyes_closed_frames += 1
                        self.continuous_sleep_time += 1/30
                        
                        # Only mark as drowsy if eyes have been closed for more than 1 second
                        if self.continuous_sleep_time > 1.0:
                            drowsy = True
                        
                        if self.eyes_closed_frames == 3:
                            self.stats["blink_count"] += 1
                            blink_detected = True
                            # Only log every 10th blink to reduce spam
                            if self.stats["blink_count"] % 10 == 0:
                                print(f"👁️ Blinks: {self.stats['blink_count']}")
                    else:
                        if self.eyes_closed_frames > 0 and self.continuous_sleep_time > 1.0:
                            print(f"👁️ Eyes opened after {self.continuous_sleep_time:.1f}s")
                        self.eyes_closed_frames = 0
                        self.continuous_sleep_time = max(0, self.continuous_sleep_time - 0.05)
                    
                    # Yawn detection
                    if mar > 0.6:
                        self.yawn_frames += 1
                        if self.yawn_frames == 10:
                            self.stats["yawn_count"] += 1
                            yawn_detected = True
                            print(f"🥱 Yawn detected! Total: {self.stats['yawn_count']}")
                    else:
                        self.yawn_frames = 0
                    
                    # Clean interface - no text overlays on OpenCV window
                    # All data is shown on web dashboard instead
                
                # Handle alerts
                if self.continuous_sleep_time >= self.config.get('emergency_threshold', 3.0):
                    print(f"🚨 ALERT! Continuous sleep: {self.continuous_sleep_time:.1f}s")
                    self.handle_drowsiness_alert(self.continuous_sleep_time)
                    # Play sound alert
                    try:
                        winsound.Beep(1000, 500)  # 1000Hz for 500ms
                    except:
                        pass
                
                # Show OpenCV window
                cv2.imshow('Drowsiness Detection - PC Mode', frame)
                
                # Update stats
                self.stats["continuous_sleep"] = round(self.continuous_sleep_time, 2)
                
                # Send stats to cloud (every 5 seconds)
                if self.cloud_client and self.stats["frames_processed"] % 150 == 0:
                    try:
                        self.cloud_client.send_stats(self.stats, self.current_location)
                    except Exception as e:
                        pass  # Silent fail for stats
                
                # Send data to web dashboard
                socketio.emit('pc_mode_data', {
                    'drowsy': bool(drowsy),
                    'continuous_sleep': round(self.continuous_sleep_time, 2),
                    'blink_detected': blink_detected,
                    'yawn_detected': yawn_detected,
                    'fps': self.stats["fps"],
                    'ear': round(ear, 3) if 'ear' in locals() else 0,
                    'mar': round(mar, 3) if 'mar' in locals() else 0,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            print(f"❌ PC Detection error: {e}")
        finally:
            face_mesh.close()
            if self.camera:
                self.camera.release()
            cv2.destroyAllWindows()
            print("🛑 PC Detection ended")
    
    def web_detection_loop(self):
        """Web-based detection (browser streaming)"""
        print("🌐 Web Detection loop started")
        
        # Initialize camera
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        # FPS tracking
        fps_counter = 0
        fps_start_time = time.time()
        
        try:
            while self.detection_active and self.camera:
                loop_start = time.time()
                
                ret, frame = self.camera.read()
                if not ret:
                    time.sleep(0.01)
                    continue
                
                # FPS calculation
                fps_counter += 1
                if fps_counter % 30 == 0:
                    current_time = time.time()
                    current_fps = 30 / (current_time - fps_start_time)
                    fps_start_time = current_time
                    self.stats["fps"] = round(current_fps, 1)
                
                self.stats["frames_processed"] += 1
                
                # Simple detection flags
                drowsy = False
                blink_detected = False
                yawn_detected = False
                
                try:
                    # Create MediaPipe instance for each frame to avoid timestamp issues
                    with self.mp_face_mesh.FaceMesh(
                        max_num_faces=1,
                        refine_landmarks=True,
                        min_detection_confidence=0.5,
                        min_tracking_confidence=0.5
                    ) as face_mesh:
                        
                        # Face detection
                        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = face_mesh.process(image_rgb)

                        if results.multi_face_landmarks:
                            face_landmarks = results.multi_face_landmarks[0]
                            
                            # Calculate EAR and MAR
                            ear = self.calculate_ear(face_landmarks)
                            mar = self.calculate_mar(face_landmarks)
                            
                            # Eye closure detection
                            if ear < 0.25:
                                self.eyes_closed_frames += 1
                                self.continuous_sleep_time += 1/30
                                
                                # Only mark as drowsy if eyes have been closed for more than 1 second
                                if self.continuous_sleep_time > 1.0:
                                    drowsy = True
                                
                                if self.eyes_closed_frames == 3:
                                    self.stats["blink_count"] += 1
                                    blink_detected = True
                                    # Only log every 10th blink to reduce spam
                                    if self.stats["blink_count"] % 10 == 0:
                                        print(f"👁️ Blinks: {self.stats['blink_count']}")
                            else:
                                if self.eyes_closed_frames > 0 and self.continuous_sleep_time > 1.0:
                                    print(f"👁️ Eyes opened after {self.continuous_sleep_time:.1f}s")
                                self.eyes_closed_frames = 0
                                self.continuous_sleep_time = max(0, self.continuous_sleep_time - 0.05)
                            
                            # Yawn detection
                            if mar > 0.6:
                                self.yawn_frames += 1
                                if self.yawn_frames == 10:
                                    self.stats["yawn_count"] += 1
                                    yawn_detected = True
                                    print(f"🥱 Yawn detected! Total: {self.stats['yawn_count']}")
                            else:
                                self.yawn_frames = 0

                except Exception as e:
                    print(f"⚠️ Web detection error: {e}")
                
                # Update stats
                self.stats["continuous_sleep"] = round(self.continuous_sleep_time, 2)
                
                # Handle drowsiness alert
                if self.continuous_sleep_time >= self.config.get('emergency_threshold', 3.0):
                    print(f"🚨 ALERT! Continuous sleep: {self.continuous_sleep_time:.1f}s")
                    self.handle_drowsiness_alert(self.continuous_sleep_time)
                
                # Encode frame for streaming
                import base64
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
                _, buffer = cv2.imencode('.jpg', frame, encode_params)
                frame_data = base64.b64encode(buffer).decode('utf-8')
                
                # Emit frame with detection data
                socketio.emit('web_mode_data', {
                    'frame': frame_data,
                    'drowsy': bool(drowsy),
                    'continuous_sleep': round(self.continuous_sleep_time, 2),
                    'blink_detected': blink_detected,
                    'yawn_detected': yawn_detected,
                    'fps': self.stats["fps"],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Maintain target FPS (limit to ~15 FPS for web mode)
                loop_time = time.time() - loop_start
                target_time = 0.067  # ~15 FPS
                if loop_time < target_time:
                    time.sleep(target_time - loop_time)
                
        except Exception as e:
            print(f"❌ Web detection error: {e}")
        finally:
            if self.camera:
                self.camera.release()
            print("🛑 Web detection ended")
    
    def stop_detection(self):
        """Stop detection"""
        print("🛑 Stopping detection...")
        self.detection_active = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        cv2.destroyAllWindows()
        print("✅ Detection stopped")

# Global detector instance
detector = HybridDrowsinessDetector()

# Flask routes
@app.route('/')
def index():
    """Main dashboard"""
    return render_template('hybrid_index.html')

@app.route('/admin')
def admin():
    """Admin settings page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html', config=detector.config)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == detector.config.get('admin_password', 'admin123'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error="Invalid password")
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/api/start_pc_mode', methods=['POST'])
def start_pc_mode():
    """Start PC mode"""
    try:
        success = detector.start_pc_mode()
        return jsonify({"success": success, "mode": "pc"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/start_web_mode', methods=['POST'])
def start_web_mode():
    """Start web mode"""
    try:
        success = detector.start_web_mode()
        return jsonify({"success": success, "mode": "web"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stop_detection', methods=['POST'])
def stop_detection():
    """Stop detection"""
    try:
        detector.stop_detection()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/status')
def get_status():
    """Get system status"""
    session_duration = (datetime.now() - detector.stats["session_start"]).total_seconds()
    
    return jsonify({
        "detection_active": detector.detection_active,
        "mode": detector.mode,
        "telegram_configured": detector.telegram_bot is not None,
        "stats": detector.stats,
        "location": detector.current_location,
        "session_duration": round(session_duration, 1)
    })

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Handle configuration"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == 'POST':
        data = request.json
        
        # Update configuration
        for key in ['bot_token', 'emergency_threshold', 'max_alerts_per_5min', 'admin_password']:
            if key in data:
                detector.config[key] = data[key]
        
        # Handle chat IDs
        if 'chat_ids' in data:
            detector.config['chat_ids'] = data['chat_ids']
        
        # Save configuration
        detector.save_config()
        
        # Reinitialize Telegram bot
        detector.setup_telegram_bot()
        
        return jsonify({"success": True})
    
    return jsonify(detector.config)

@app.route('/api/test_telegram', methods=['POST'])
def test_telegram():
    """Test Telegram configuration"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    if detector.telegram_bot:
        success = detector.telegram_bot.send_message("🧪 Test message from Hybrid Drowsiness Detection System")
        return jsonify({"success": success})
    
    return jsonify({"success": False, "error": "Telegram not configured"})

@app.route('/api/get_telegram_updates')
def get_telegram_updates():
    """Get Telegram bot updates to find chat IDs"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    bot_token = detector.config.get('bot_token')
    if not bot_token:
        return jsonify({"error": "Bot token not configured"})
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                # Extract unique chat IDs and user info
                chats = {}
                for update in data['result']:
                    if 'message' in update:
                        msg = update['message']
                        chat_id = str(msg['chat']['id'])
                        chat_info = {
                            'id': chat_id,
                            'type': msg['chat']['type'],
                            'first_name': msg['chat'].get('first_name', ''),
                            'last_name': msg['chat'].get('last_name', ''),
                            'username': msg['chat'].get('username', ''),
                            'last_message': msg.get('text', '')[:50]
                        }
                        chats[chat_id] = chat_info
                
                return jsonify({"success": True, "chats": list(chats.values())})
        
        return jsonify({"success": False, "error": "Failed to get updates"})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print("🚀 Starting Hybrid Drowsiness Detection System...")
    print("📱 Access the dashboard at: http://localhost:5000")
    print("🎯 Choose between PC Mode (high performance) or Web Mode")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)