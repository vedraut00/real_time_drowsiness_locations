import queue
import threading
import time
import winsound
import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
import sys
import os
import json
import requests
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QHBoxLayout, 
                           QWidget, QVBoxLayout, QPushButton, QMessageBox, QDialog)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt

class TelegramBot:
    """Simple Telegram bot for emergency alerts - supports multiple recipients"""
    def __init__(self, bot_token=None, chat_ids=None, max_alerts=5):
        self.bot_token = bot_token
        # Handle both single chat_id and multiple chat_ids for backward compatibility
        if isinstance(chat_ids, str):
            self.chat_ids = [chat_ids]
        elif isinstance(chat_ids, list):
            self.chat_ids = chat_ids
        else:
            self.chat_ids = []
        
        self.enabled = bool(bot_token and self.chat_ids)
        
        # Alert limiting to prevent spam
        self.max_alerts = max_alerts
        self.alert_count = 0
        self.last_reset_time = time.time()
        self.reset_interval = 300  # Reset counter every 5 minutes
        
    def send_message(self, message):
        """Send message to all configured recipients"""
        if not self.enabled:
            return False
            
        success_count = 0
        for chat_id in self.chat_ids:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, data=data, timeout=10)
                if response.status_code == 200:
                    success_count += 1
                else:
                    print(f"❌ Telegram send failed to {chat_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Telegram send failed to {chat_id}: {e}")
        
        return success_count > 0
    
    def get_current_location(self):
        """Get current location using IP geolocation"""
        try:
            # Use a free IP geolocation service
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    city = data.get('city', 'Unknown')
                    region = data.get('regionName', 'Unknown')
                    country = data.get('country', 'Unknown')
                    lat = data.get('lat', 0)
                    lon = data.get('lon', 0)
                    
                    location_text = f"{city}, {region}, {country}"
                    google_maps_link = f"https://maps.google.com/?q={lat},{lon}"
                    
                    return location_text, google_maps_link
        except Exception as e:
            print(f"❌ Location fetch failed: {e}")
        
        return "Location unavailable", None
    
    def reset_alert_counter_if_needed(self):
        """Reset alert counter every 5 minutes"""
        current_time = time.time()
        if current_time - self.last_reset_time > self.reset_interval:
            self.alert_count = 0
            self.last_reset_time = current_time
            print("🔄 Alert counter reset")
    
    def send_emergency_alert(self, microsleep_duration, location="Unknown"):
        """Send emergency drowsiness alert to all recipients (limited to prevent spam)"""
        # Reset counter if needed
        self.reset_alert_counter_if_needed()
        
        # Check if we've reached the alert limit
        if self.alert_count >= self.max_alerts:
            print(f"⚠️ Alert limit reached ({self.max_alerts}/5 min). Skipping to prevent spam.")
            return False
        
        # Get live location
        location_text, maps_link = self.get_current_location()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create message with live location
        message = (
            f"🚨 <b>DROWSINESS EMERGENCY ALERT</b> 🚨\n\n"
            f"⚠️ <b>Critical microsleep detected!</b>\n"
            f"⏱️ Duration: <b>{microsleep_duration:.1f} seconds</b>\n"
            f"📍 Location: <b>{location_text}</b>\n"
        )
        
        if maps_link:
            message += f"🗺️ <a href='{maps_link}'>View on Google Maps</a>\n"
        
        message += (
            f"🕐 Time: {timestamp}\n"
            f"📊 Alert: {self.alert_count + 1}/{self.max_alerts} (5 min)\n\n"
            f"🚗 <b>DRIVER NEEDS IMMEDIATE ATTENTION!</b>\n"
            f"Please check on the driver immediately."
        )
        
        success = self.send_message(message)
        if success:
            self.alert_count += 1
            print(f"🚨 Emergency alert sent to {len(self.chat_ids)} recipient(s) ({self.alert_count}/{self.max_alerts})")
        return success

class DeviceSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.device_choice = 'cpu'
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Drowsiness Detection - Device Selection")
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Choose Processing Device")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2E7D32; margin: 20px;")
        layout.addWidget(title)
        
        # Check CUDA availability
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                gpu_name = torch.cuda.get_device_name(0)
                status_text = f"✅ GPU Available: {gpu_name}"
                status_color = "color: green;"
            else:
                status_text = "⚠️ GPU Not Available - CUDA not detected"
                status_color = "color: orange;"
        except ImportError:
            cuda_available = False
            status_text = "❌ PyTorch not installed - GPU unavailable"
            status_color = "color: red;"
        
        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet(f"{status_color} margin: 10px;")
        layout.addWidget(status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        gpu_btn = QPushButton("🚀 Use GPU (Faster)")
        gpu_btn.setEnabled(cuda_available)
        gpu_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        gpu_btn.clicked.connect(lambda: self.select_device('cuda'))
        
        cpu_btn = QPushButton("💻 Use CPU (Compatible)")
        cpu_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        cpu_btn.clicked.connect(lambda: self.select_device('cpu'))
        
        button_layout.addWidget(gpu_btn)
        button_layout.addWidget(cpu_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def select_device(self, device):
        self.device_choice = device
        self.accept()

class DrowsinessDetector(QMainWindow):
    def __init__(self, device='cpu'):
        super().__init__()
        
        # Device setup
        self.device = device
        self.setup_device()
        
        # Detection states
        self.yawn_state = ''
        self.left_eye_state = ''
        self.right_eye_state = ''
        self.alert_text = ''

        # Counters
        self.blinks = 0
        self.microsleeps = 0
        self.yawns = 0
        self.yawn_duration = 0 

        # State tracking
        self.left_eye_still_closed = False  
        self.right_eye_still_closed = False 
        self.yawn_in_progress = False  
        
        # Initialize MediaPipe
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7,
            max_num_faces=1
        )
        self.points_ids = [187, 411, 152, 68, 174, 399, 298]

        # UI Setup
        device_name = "GPU" if device == 'cuda' else "CPU"
        self.setWindowTitle(f"Drowsiness Detection - {device_name} Mode")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("background-color: white;")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Video display
        self.video_label = QLabel(self)
        self.video_label.setStyleSheet("border: 2px solid black;")
        self.video_label.setFixedSize(640, 480)
        self.layout.addWidget(self.video_label)

        # Info panel
        self.info_label = QLabel()
        self.info_label.setStyleSheet("background-color: white; border: 1px solid black; padding: 10px;")
        self.layout.addWidget(self.info_label)

        # Initialize performance monitoring
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0

        # Initialize Telegram bot
        self.telegram_bot = None
        self.emergency_threshold = 4.0  # seconds
        self.setup_telegram_bot()

        self.update_info()
        
        # Load models
        self.load_models()
        
        # Initialize camera
        self.setup_camera()

        # Threading
        self.frame_queue = queue.Queue(maxsize=2)
        self.stop_event = threading.Event()
        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.process_thread = threading.Thread(target=self.process_frames)

        self.capture_thread.start()
        self.process_thread.start()
    
    def setup_telegram_bot(self):
        """Setup Telegram bot for emergency alerts"""
        config_file = "telegram_config.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                bot_token = config.get('bot_token')
                # Support both single chat_id and multiple chat_ids
                chat_ids = config.get('chat_ids', config.get('chat_id'))
                self.emergency_threshold = config.get('emergency_threshold', 4.0)
                
                if bot_token and chat_ids:
                    self.telegram_bot = TelegramBot(bot_token, chat_ids)
                    recipient_count = len(self.telegram_bot.chat_ids) if self.telegram_bot.chat_ids else 0
                    print(f"✅ Telegram bot configured ({recipient_count} recipient(s), threshold: {self.emergency_threshold}s)")
                else:
                    print("⚠️ Telegram bot token or chat ID missing")
                    
            except Exception as e:
                print(f"❌ Telegram config error: {e}")
        else:
            print("⚠️ No telegram_config.json found - Telegram alerts disabled")
            print("💡 Run setup_telegram.bat to configure Telegram alerts")
        
    def setup_device(self):
        """Setup computing device"""
        if self.device == 'cuda':
            try:
                import torch
                if torch.cuda.is_available():
                    print(f"🚀 Using GPU: {torch.cuda.get_device_name(0)}")
                    print(f"CUDA Version: {torch.version.cuda}")
                    print(f"Available GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
                else:
                    print("⚠️ CUDA not available, falling back to CPU")
                    self.device = 'cpu'
            except ImportError:
                print("⚠️ PyTorch not available, using CPU")
                self.device = 'cpu'
        else:
            print("💻 Using CPU mode")
    
    def load_models(self):
        """Load YOLO models"""
        print("Loading YOLO models...")
        
        # Check if model files exist
        yawn_model_path = "runs/detectyawn/train/weights/best.pt"
        eye_model_path = "runs/detecteye/train/weights/best.pt"
        
        if not os.path.exists(yawn_model_path) or not os.path.exists(eye_model_path):
            QMessageBox.critical(self, "Model Error", 
                               "Model files not found!\nPlease ensure the trained models are in:\n"
                               f"- {yawn_model_path}\n- {eye_model_path}")
            sys.exit(1)
        
        try:
            self.detectyawn = YOLO(yawn_model_path)
            self.detecteye = YOLO(eye_model_path)
            
            # Move models to device if GPU
            if self.device == 'cuda':
                self.detectyawn.to(self.device)
                self.detecteye.to(self.device)
                print("✅ Models loaded on GPU")
            else:
                print("✅ Models loaded on CPU")
                
        except Exception as e:
            QMessageBox.critical(self, "Model Loading Error", f"Failed to load models: {str(e)}")
            sys.exit(1)
    
    def setup_camera(self):
        """Initialize camera with optimal settings"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Camera Error", "Could not open camera!")
            sys.exit(1)
            
        # Optimize camera settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        time.sleep(1.0)
        print("✅ Camera initialized")
        
    def update_info(self):
        """Update information panel"""
        # Alert logic with emergency notifications
        emergency_triggered = False
        
        if round(self.yawn_duration, 2) > 3.0:
            self.alert_text = "<p style='color: orange; font-weight: bold;'>⚠️ Alert: Prolonged Yawn Detected!</p>"
        elif round(self.microsleeps, 2) > self.emergency_threshold:
            self.alert_text = "<p style='color: red; font-weight: bold;'>🚨 EMERGENCY: Critical Microsleep Detected!</p>"
            emergency_triggered = True
        elif round(self.microsleeps, 2) > 2.0:
            self.alert_text = "<p style='color: red; font-weight: bold;'>🚨 DANGER: Microsleep Detected!</p>"
        elif self.microsleeps < 1.0 and self.yawn_duration < 2.0:
            self.alert_text = ""
        
        # Trigger emergency alerts if threshold exceeded
        if emergency_triggered and self.telegram_bot and self.telegram_bot.enabled:
            threading.Thread(
                target=self.trigger_emergency_alert,
                daemon=True
            ).start()

        device_display = "🚀 GPU" if self.device == 'cuda' else "💻 CPU"
        emergency_status = "🚨 ON" if (self.telegram_bot and self.telegram_bot.enabled) else "❌ OFF"
        
        info_text = (
            f"<div style='font-family: Arial, sans-serif; color: #333;'>"
            f"<h2 style='text-align: center; color: #4CAF50;'>Drowsiness Detector</h2>"
            f"<p style='text-align: center; color: #666;'>Device: {device_display} | FPS: {self.current_fps:.1f}</p>"
            f"<p style='text-align: center; color: #666;'>Emergency Alerts: {emergency_status} | Threshold: {self.emergency_threshold}s</p>"
            f"<hr style='border: 1px solid #4CAF50;'>"
            f"{self.alert_text}"
            f"<p><b>👁️ Blinks:</b> {self.blinks}</p>"
            f"<p><b>💤 Microsleeps:</b> {round(self.microsleeps,2)} seconds</p>"
            f"<p><b>😮 Yawns:</b> {self.yawns}</p>"
            f"<p><b>⏳ Yawn Duration:</b> {round(self.yawn_duration,2)} seconds</p>"
            f"<hr style='border: 1px solid #4CAF50;'>"
            f"</div>"
        )
        self.info_label.setText(info_text)

    def predict_eye(self, eye_frame, eye_state):
        """Predict eye state (open/closed)"""
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
        """Predict yawn state"""
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

    def capture_frames(self):
        """Capture frames from camera"""
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if ret:
                if self.frame_queue.qsize() < 2:
                    self.frame_queue.put(frame)
            else:
                break

    def process_frames(self):
        """Process captured frames"""
        while not self.stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=1)
                
                # FPS calculation
                self.fps_counter += 1
                if self.fps_counter % 30 == 0:
                    current_time = time.time()
                    self.current_fps = 30 / (current_time - self.fps_start_time)
                    self.fps_start_time = current_time
                
                # Face detection
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(image_rgb)

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        ih, iw, _ = frame.shape
                        points = []

                        for point_id in self.points_ids:
                            lm = face_landmarks.landmark[point_id]
                            x, y = int(lm.x * iw), int(lm.y * ih)
                            points.append((x, y))

                        if len(points) == 7:
                            # Extract ROI coordinates
                            x1, y1 = points[0]  
                            x2, _ = points[1]  
                            _, y3 = points[2]  
                            x4, y4 = points[3]  
                            x5, y5 = points[4]  
                            x6, y6 = points[5]  
                            x7, y7 = points[6]  

                            # Ensure proper bounds
                            x6, x7 = min(x6, x7), max(x6, x7)
                            y6, y7 = min(y6, y7), max(y6, y7)
                            
                            # Extract ROIs with padding
                            padding = 5
                            mouth_roi = frame[max(0, y1-padding):min(ih, y3+padding), 
                                            max(0, x1-padding):min(iw, x2+padding)]
                            right_eye_roi = frame[max(0, y4-padding):min(ih, y5+padding), 
                                                max(0, x4-padding):min(iw, x5+padding)]
                            left_eye_roi = frame[max(0, y6-padding):min(ih, y7+padding), 
                                               max(0, x6-padding):min(iw, x7+padding)]

                            # Predictions
                            self.left_eye_state = self.predict_eye(left_eye_roi, self.left_eye_state)
                            self.right_eye_state = self.predict_eye(right_eye_roi, self.right_eye_state)
                            self.predict_yawn(mouth_roi)

                            # Drowsiness logic
                            if self.left_eye_state == "Close Eye" and self.right_eye_state == "Close Eye":
                                if not self.left_eye_still_closed and not self.right_eye_still_closed:
                                    self.left_eye_still_closed, self.right_eye_still_closed = True, True
                                    self.blinks += 1 
                                self.microsleeps += 1/30
                            else:
                                if self.left_eye_still_closed and self.right_eye_still_closed:
                                    self.left_eye_still_closed, self.right_eye_still_closed = False, False
                                self.microsleeps = max(0, self.microsleeps - 0.1)

                            if self.yawn_state == "Yawn":
                                if not self.yawn_in_progress:
                                    self.yawn_in_progress = True
                                    self.yawns += 1  
                                self.yawn_duration += 1/30
                            else:
                                if self.yawn_in_progress:
                                    self.yawn_in_progress = False
                                    self.yawn_duration = 0

                            self.update_info()
                            self.display_frame(frame)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")

    def display_frame(self, frame):
        """Display frame in GUI"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        self.video_label.setPixmap(QPixmap.fromImage(p))

    def trigger_emergency_alert(self):
        """Trigger emergency alert via Telegram"""
        try:
            if self.telegram_bot and self.telegram_bot.enabled:
                # Get current location (you could integrate GPS here)
                location = "Driver Location Unknown"
                
                # Send emergency alert
                success = self.telegram_bot.send_emergency_alert(
                    self.microsleeps, 
                    location
                )
                
                if success:
                    print(f"🚨 TELEGRAM ALERT SENT: Microsleep {self.microsleeps:.1f}s")
                    # Play emergency sound
                    try:
                        winsound.Beep(1000, 1000)  # 1000Hz for 1 second
                    except:
                        pass
                else:
                    print(f"❌ Telegram alert failed")
                
        except Exception as e:
            print(f"❌ Emergency alert failed: {e}")

    def closeEvent(self, event):
        """Clean shutdown"""
        self.stop_event.set()
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Device selection dialog
    selector = DeviceSelector()
    if selector.exec_() == QDialog.Accepted:
        device = selector.device_choice
        
        # Launch detector
        window = DrowsinessDetector(device=device)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()