#!/usr/bin/env python3
"""
Drowsiness Detection Web Interface
Real-time monitoring with admin controls and Google Maps integration
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
import cv2
import base64
import threading
import time
import json
import os
import requests
from datetime import datetime
import queue
from DrowsinessDetector_Universal import TelegramBot
import numpy as np
from ultralytics import YOLO
import mediapipe as mp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'drowsiness_detection_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebDrowsinessDetector:
    def __init__(self):
        self.camera = None
        self.detection_active = False
        self.telegram_bot = None
        self.config = self.load_config()
        self.alert_queue = queue.Queue()
        self.current_location = {"lat": 0, "lng": 0, "address": "Unknown"}
        
        # Enhanced statistics with detailed metrics
        self.stats = {
            "total_alerts": 0,
            "session_alerts": 0,
            "last_alert": None,
            "session_start": datetime.now(),
            "blink_count": 0,
            "yawn_count": 0,
            "total_blinks": 0,
            "total_yawns": 0,
            "avg_ear": 0.0,
            "avg_mar": 0.0,
            "fps": 0,
            "frames_processed": 0
        }
        
        # Detection parameters
        self.EAR_THRESHOLD = 0.25
        self.MAR_THRESHOLD = 0.7
        self.BLINK_FRAMES = 3
        self.YAWN_FRAMES = 20
        
        # Counters for detection
        self.blink_counter = 0
        self.yawn_counter = 0
        self.ear_values = []
        self.mar_values = []
        
        # Performance tracking
        self.last_fps_time = time.time()
        self.frame_count = 0
        
        # Initialize models
        self.setup_models()
        self.setup_telegram_bot()
        
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
                    # Merge with defaults for missing keys
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
        """Initialize detection models using original proven algorithm"""
        try:
            # Initialize MediaPipe Face Mesh
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Face mesh points for ROI extraction (original configuration)
            self.points_ids = [13, 14, 15, 33, 7, 163, 144]
            
            # Detection states (original variables)
            self.left_eye_state = "Open Eye"
            self.right_eye_state = "Open Eye"
            self.yawn_state = "No Yawn"
            self.left_eye_still_closed = False
            self.right_eye_still_closed = False
            self.yawn_in_progress = False
            self.microsleeps = 0.0
            self.yawn_duration = 0.0
            
            # Device detection
            import torch
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            # Try to load YOLO models for eye and yawn detection
            try:
                self.detecteye = YOLO('eye_model.pt')
                self.detectyawn = YOLO('yawn_model.pt')
                print("✅ Original YOLO models loaded successfully")
            except:
                # Fallback to EAR/MAR detection if original models not found
                print("⚠️ Original models not found, using EAR/MAR fallback detection")
                self.detecteye = None
                self.detectyawn = None
            
            print("✅ Models loaded successfully")
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            # Initialize fallback variables
            self.detecteye = None
            self.detectyawn = None
            self.points_ids = [13, 14, 15, 33, 7, 163, 144]
            self.left_eye_state = "Open Eye"
            self.right_eye_state = "Open Eye"
            self.yawn_state = "No Yawn"
            self.left_eye_still_closed = False
            self.right_eye_still_closed = False
            self.yawn_in_progress = False
            self.microsleeps = 0.0
            self.yawn_duration = 0.0
    
    def setup_telegram_bot(self):
        """Setup Telegram bot with current config"""
        if self.config.get('bot_token') and self.config.get('chat_ids'):
            self.telegram_bot = TelegramBot(
                self.config['bot_token'],
                self.config['chat_ids'],
                self.config.get('max_alerts_per_5min', 5)
            )
            print("✅ Telegram bot configured")
        else:
            print("⚠️ Telegram bot not configured")
    
    def get_current_location(self):
        """Get current location using IP geolocation"""
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
    
    def start_detection(self):
        """Start camera and detection"""
        if self.detection_active:
            print("⚠️ Detection already active")
            return True  # Return True if already active
        
        try:
            # Release any existing camera
            if self.camera:
                self.camera.release()
            
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("❌ Camera not available")
                return False
            
            # Set camera properties for optimal performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize lag
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))  # Use MJPEG for better performance
            
            self.detection_active = True
            self.stats["session_start"] = datetime.now()
            self.stats["session_alerts"] = 0
            
            # Reinitialize MediaPipe to avoid timestamp issues
            self.setup_models()
            
            # Start detection thread
            detection_thread = threading.Thread(target=self.detection_loop)
            detection_thread.daemon = True
            detection_thread.start()
            
            print("✅ Detection started successfully")
            return True
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            self.detection_active = False
            return False
    
    def stop_detection(self):
        """Stop detection and release camera"""
        print("🛑 Stopping detection...")
        self.detection_active = False
        
        # Give threads time to stop
        time.sleep(0.5)
        
        if self.camera:
            self.camera.release()
            self.camera = None
            
        print("✅ Detection stopped")
    
    def detection_loop(self):
        """Simplified robust detection loop"""
        print("🎥 Detection loop started with simplified algorithm")
        
        # FPS tracking
        fps_counter = 0
        fps_start_time = time.time()
        
        # Detection variables
        eyes_closed_frames = 0
        yawn_frames = 0
        continuous_sleep_time = 0.0
        
        try:
            while self.detection_active and self.camera:
                loop_start = time.time()
                
                ret, frame = self.camera.read()
                if not ret:
                    print("⚠️ Failed to read frame")
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
                    # Create a new MediaPipe instance for each frame to avoid timestamp issues
                    with mp.solutions.face_mesh.FaceMesh(
                        max_num_faces=1,
                        refine_landmarks=True,
                        min_detection_confidence=0.5,
                        min_tracking_confidence=0.5
                    ) as face_mesh:
                        
                        # Face detection using MediaPipe
                        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = face_mesh.process(image_rgb)

                        if results.multi_face_landmarks:
                            face_landmarks = results.multi_face_landmarks[0]
                            
                            # Simple EAR/MAR calculation
                            ear = self.calculate_ear_simple(face_landmarks)
                            mar = self.calculate_mar_simple(face_landmarks)
                            
                            # Eye closure detection
                            if ear < 0.25:  # Eyes closed
                                eyes_closed_frames += 1
                                continuous_sleep_time += 1/30  # Add frame time
                                
                                # Only mark as drowsy if eyes have been closed for more than 1 second
                                if continuous_sleep_time > 1.0:
                                    drowsy = True
                                
                                # Detect blink (short closure) - only log every 10th to reduce spam
                                if eyes_closed_frames == 3:  # Just closed
                                    self.stats["blink_count"] += 1
                                    self.stats["total_blinks"] += 1
                                    blink_detected = True
                                    if self.stats["blink_count"] % 10 == 0:
                                        print(f"👁️ Blinks: {self.stats['blink_count']}")
                                    
                            else:  # Eyes open
                                if eyes_closed_frames > 0 and continuous_sleep_time > 1.0:
                                    print(f"👁️ Eyes opened after {continuous_sleep_time:.1f}s")
                                eyes_closed_frames = 0
                                continuous_sleep_time = max(0, continuous_sleep_time - 0.05)  # Gradual decrease
                            
                            # Yawn detection
                            if mar > 0.6:  # Yawn threshold (lowered for better detection)
                                yawn_frames += 1
                                if yawn_frames == 10:  # Just started yawning
                                    self.stats["yawn_count"] += 1
                                    self.stats["total_yawns"] += 1
                                    yawn_detected = True
                                    print(f"🥱 Yawn detected! Total: {self.stats['yawn_count']}")
                            else:
                                yawn_frames = 0
                            
                            # Update stats
                            self.stats["avg_ear"] = round(continuous_sleep_time, 2)
                            self.stats["avg_mar"] = round(mar, 3)

                except Exception as e:
                    print(f"⚠️ Detection error: {e}")
                    # Continue without detection for this frame
                
                # Handle drowsiness alert
                if continuous_sleep_time >= self.config.get('emergency_threshold', 3.0):
                    print(f"🚨 ALERT! Continuous sleep: {continuous_sleep_time:.1f}s")
                    self.handle_drowsiness_alert(continuous_sleep_time)
                    # Don't reset here, let it continue counting
                
                # Encode frame for streaming (clean feed)
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
                _, buffer = cv2.imencode('.jpg', frame, encode_params)
                frame_data = base64.b64encode(buffer).decode('utf-8')
                
                # Emit frame with detection data
                socketio.emit('video_frame', {
                    'frame': frame_data,
                    'drowsy': bool(drowsy),
                    'continuous_sleep': round(continuous_sleep_time, 2),
                    'blink_detected': blink_detected,
                    'yawn_detected': yawn_detected,
                    'fps': self.stats["fps"],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Maintain target FPS
                loop_time = time.time() - loop_start
                target_time = 0.033
                if loop_time < target_time:
                    time.sleep(target_time - loop_time)
                
        except Exception as e:
            print(f"❌ Detection loop error: {e}")
        finally:
            print("🛑 Detection loop ended")
    
    def predict_eye(self, eye_frame, eye_state):
        """Original eye prediction method"""
        if eye_frame.size == 0:
            return eye_state
            
        try:
            # Inference settings based on device
            conf_threshold = 0.25 if self.device == 'cuda' else 0.3
            
            results_eye = self.detecteye.predict(
                eye_frame, 
                device=self.device,
                verbose=False,
                conf=conf_threshold,
                iou=0.45
            )
            
            boxes = results_eye[0].boxes
            if len(boxes) == 0:
                return eye_state

            confidences = boxes.conf.cpu().numpy()  
            class_ids = boxes.cls.cpu().numpy()  
            max_confidence_index = np.argmax(confidences)
            class_id = int(class_ids[max_confidence_index])
            confidence = confidences[max_confidence_index]

            if class_id == 1 and confidence > 0.3:  # Closed eye
                eye_state = "Close Eye"
            elif class_id == 0 and confidence > 0.25:  # Open eye
                eye_state = "Open Eye"
                                
        except Exception as e:
            print(f"Eye prediction error: {e}")
            
        return eye_state

    def predict_yawn(self, yawn_frame):
        """Original yawn prediction method"""
        if yawn_frame.size == 0:
            return
            
        try:
            conf_threshold = 0.3 if self.device == 'cuda' else 0.35
            
            results_yawn = self.detectyawn.predict(
                yawn_frame,
                device=self.device,
                verbose=False,
                conf=conf_threshold,
                iou=0.45
            )
            
            boxes = results_yawn[0].boxes
            if len(boxes) == 0:
                return

            confidences = boxes.conf.cpu().numpy()  
            class_ids = boxes.cls.cpu().numpy()  
            max_confidence_index = np.argmax(confidences)
            class_id = int(class_ids[max_confidence_index])
            confidence = confidences[max_confidence_index]

            if class_id == 0 and confidence > 0.4:  # Yawn
                self.yawn_state = "Yawn"
            elif class_id == 1 and confidence > 0.3:  # No yawn
                self.yawn_state = "No Yawn"
                
        except Exception as e:
            print(f"Yawn prediction error: {e}")
    
    def calculate_ear_fallback(self, landmarks):
        """Fallback EAR calculation using MediaPipe landmarks"""
        try:
            # Left eye landmarks
            left_eye = [33, 7, 163, 144, 145, 153]
            # Right eye landmarks  
            right_eye = [362, 382, 381, 380, 374, 373]
            
            def get_ear(eye_points):
                # Get coordinates
                coords = []
                for i in eye_points:
                    lm = landmarks.landmark[i]
                    coords.append([lm.x, lm.y])
                coords = np.array(coords)
                
                # Calculate distances
                # Vertical distances
                v1 = np.linalg.norm(coords[1] - coords[5])
                v2 = np.linalg.norm(coords[2] - coords[4])
                
                # Horizontal distance
                h = np.linalg.norm(coords[0] - coords[3])
                
                # EAR calculation
                if h > 0:
                    return (v1 + v2) / (2.0 * h)
                return 0.3
            
            # Calculate EAR for both eyes
            left_ear = get_ear(left_eye)
            right_ear = get_ear(right_eye)
            
            return (left_ear + right_ear) / 2.0
            
        except Exception as e:
            return 0.3
    
    def calculate_mar_fallback(self, landmarks):
        """Fallback MAR calculation using MediaPipe landmarks"""
        try:
            # Mouth landmarks
            mouth_points = [61, 84, 17, 314, 405, 320, 307, 375]
            
            # Get coordinates
            coords = []
            for i in mouth_points:
                lm = landmarks.landmark[i]
                coords.append([lm.x, lm.y])
            coords = np.array(coords)
            
            # Calculate vertical distances
            v1 = np.linalg.norm(coords[2] - coords[6])  # Top to bottom
            v2 = np.linalg.norm(coords[3] - coords[7])  # Top to bottom
            
            # Calculate horizontal distance
            h = np.linalg.norm(coords[0] - coords[1])  # Left to right
            
            # MAR calculation
            if h > 0:
                return (v1 + v2) / (2.0 * h)
            return 0.0
            
        except Exception as e:
            return 0.0
    
    def calculate_ear_simple(self, landmarks):
        """Simple EAR calculation"""
        try:
            # Left eye landmarks (simplified)
            left_eye = [33, 160, 158, 133, 153, 144]
            # Right eye landmarks (simplified)
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
    
    def calculate_mar_simple(self, landmarks):
        """Simple MAR calculation"""
        try:
            # Mouth landmarks (simplified)
            mouth_points = [13, 14, 269, 270, 267, 271, 272, 17]
            
            coords = []
            for i in mouth_points:
                lm = landmarks.landmark[i]
                coords.append([lm.x, lm.y])
            coords = np.array(coords)
            
            # Vertical distance (mouth opening)
            v1 = np.linalg.norm(coords[1] - coords[7])  # Top to bottom lip
            
            # Horizontal distance (mouth width)
            h = np.linalg.norm(coords[0] - coords[4])  # Left to right corner
            
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
        
        # Add to alert queue
        self.alert_queue.put(alert_data)
        
        # Emit to web clients
        socketio.emit('drowsiness_alert', alert_data)
        
        print(f"🚨 Drowsiness alert: {duration:.1f}s at {location['address']}")

# Global detector instance
detector = WebDrowsinessDetector()

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

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

@app.route('/api/start_detection', methods=['POST'])
def start_detection():
    """Start detection API"""
    try:
        success = detector.start_detection()
        return jsonify({"success": success})
    except Exception as e:
        print(f"❌ Start detection API error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stop_detection', methods=['POST'])
def stop_detection():
    """Stop detection API"""
    try:
        detector.stop_detection()
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Stop detection API error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/status')
def get_status():
    """Get system status with detailed metrics"""
    # Calculate session duration
    session_duration = (datetime.now() - detector.stats["session_start"]).total_seconds()
    
    return jsonify({
        "detection_active": detector.detection_active,
        "telegram_configured": detector.telegram_bot is not None,
        "stats": detector.stats,
        "location": detector.current_location,
        "detailed_metrics": {
            "session_duration": round(session_duration, 1),
            "blinks_per_minute": round((detector.stats["blink_count"] / max(session_duration / 60, 1)), 1),
            "yawns_per_minute": round((detector.stats["yawn_count"] / max(session_duration / 60, 1)), 1),
            "ear_threshold": detector.EAR_THRESHOLD,
            "mar_threshold": detector.MAR_THRESHOLD,
            "current_fps": detector.stats["fps"]
        }
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
        success = detector.telegram_bot.send_message("🧪 Test message from Drowsiness Detection System")
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

@app.route('/favicon.ico')
def favicon():
    """Simple favicon to prevent 404 errors"""
    return '', 204

if __name__ == '__main__':
    print("🌐 Starting Drowsiness Detection Web Interface...")
    print("📱 Access the dashboard at: http://localhost:5000")
    print("⚙️ Admin panel at: http://localhost:5000/admin")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)