# Drowsiness Detection System

Real-time drowsiness detection using computer vision and machine learning to monitor driver alertness and prevent accidents.

## 🚀 Quick Start

### 🐳 Docker (Recommended - Easiest)
```bash
# Windows
docker-run.bat

# Linux/Mac
chmod +x docker-run.sh
./docker-run.sh
```
Access at: http://localhost:5000

### 💻 Native Installation
1. **Run the system:**
   ```cmd
   launch.bat
   ```

2. **Setup Telegram alerts (optional):**
   ```cmd
   setup_telegram.bat
   ```

## 📁 Project Structure

```
Real_time_drowsy_driving_detection/
├── 🐳 Docker Files
│   ├── Dockerfile                    # Container image definition
│   ├── docker-compose.yml           # Container orchestration
│   ├── docker-run.bat              # Windows launcher
│   ├── docker-run.sh              # Linux/Mac launcher
│   └── DOCKER_README.md          # Docker documentation
├── 🌐 Web Interface
│   ├── web_app.py                  # Web-only mode
│   ├── hybrid_detector.py         # Hybrid PC/Web mode
│   └── templates/                # HTML templates
│       ├── index.html           # Main dashboard
│       ├── hybrid_index.html   # Hybrid dashboard
│       ├── admin.html         # Admin panel
│       └── base.html         # Base template
├── 🤖 Core System
│   ├── DrowsinessDetector_Universal.py  # Main detection engine
│   ├── setup_telegram.py              # Telegram bot setup
│   └── telegram_config.json          # Telegram configuration
├── 🚀 Launchers
│   ├── launch.bat                    # Native launcher
│   ├── start_web_app.bat           # Web mode launcher
│   └── start_hybrid.bat           # Hybrid mode launcher
└── 📦 Configuration
    ├── requirements.txt          # Python dependencies
    └── dataset.yaml            # YOLO dataset config
```

## ✨ Features

### 🎯 Detection Capabilities
- **Real-time Detection**: Monitors eye closure and yawning via webcam
- **Smart Thresholds**: Distinguishes normal blinks from drowsiness (>1 second)
- **Dual Detection**: Eye closure (EAR) and yawn detection (MAR)
- **Alert Limiting**: Prevents spam with configurable alert thresholds

### 🌐 Multiple Modes
- **Web Mode**: Browser-based interface, accessible from any device
- **Hybrid Mode**: High-performance OpenCV window + web dashboard
- **PC Mode**: Native desktop application with PyQt5 GUI

### 📱 Notifications & Tracking
- **Telegram Alerts**: Emergency notifications when critical drowsiness detected
- **Live Location**: Real-time IP geolocation with interactive maps
- **Alert History**: Track all drowsiness events with timestamps
- **Statistics Dashboard**: Blinks, yawns, session duration, and more

### ⚡ Performance
- **GPU Acceleration**: Optimized for NVIDIA RTX GPUs (falls back to CPU)
- **MediaPipe Integration**: Fast and accurate facial landmark detection
- **Efficient Streaming**: Socket.IO for real-time video and data updates
- **Docker Support**: Easy deployment with containerization

## 🔧 Installation

### Option 1: Docker (Recommended - Easiest) 🐳
```bash
# Clone repository
git clone https://github.com/vedraut00/real_time_drowsiness_locations.git
cd real_time_drowsiness_locations

# Windows
docker-run.bat

# Linux/Mac
chmod +x docker-run.sh
./docker-run.sh
```

**Benefits:**
- ✅ No Python installation needed
- ✅ No dependency conflicts
- ✅ Works on Windows, Linux, and Mac
- ✅ Easy updates and rollbacks
- ✅ Isolated environment

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker documentation.

### Option 2: Native Installation (Advanced)

#### Quick Setup
```cmd
# Clone repository
git clone https://github.com/vedraut00/real_time_drowsiness_locations.git
cd real_time_drowsiness_locations

# Run launcher - it will guide you through setup
launch.bat
```

#### Manual Setup
```cmd
# Create virtual environment
python -m venv venv_gpu
venv_gpu\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Choose your mode:
# Web Mode (browser-based)
python web_app.py

# Hybrid Mode (OpenCV + web dashboard)
python hybrid_detector.py

# Classic Mode (PyQt5 GUI)
python DrowsinessDetector_Universal.py
```

## 📱 Telegram Setup

1. **Create a bot:**
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Save your bot token

2. **Configure alerts:**
   ```cmd
   setup_telegram.bat
   ```
   - Enter your bot token
   - Send a message to your bot
   - Select your chat from the detected list

3. **Test alerts:**
   The setup will send a test message to confirm everything works.

## 🎯 How It Works

### Detection Methods

The system uses **MediaPipe Face Mesh** for facial landmark detection and calculates:

1. **EAR (Eye Aspect Ratio)**: Measures eye openness
   - Normal: > 0.25
   - Closed: < 0.25
   - Drowsy: Closed for > 1 second

2. **MAR (Mouth Aspect Ratio)**: Detects yawning
   - Normal: < 0.6
   - Yawning: > 0.6

**Optional YOLO Models** (if available):
- `eye_model.pt`: Enhanced eye state classification
- `yawn_model.pt`: Advanced yawn detection

### Detection Logic

- ✅ **Normal Blinks** (< 1 second): Counted but not flagged as drowsy
- ⚠️ **Prolonged Closure** (1-3 seconds): Marked as drowsy state
- 🚨 **Emergency Alert** (> 3 seconds): Triggers Telegram notification
- 📊 **Alert Limiting**: Max 5 alerts per 5 minutes to prevent spam

### System Modes

#### 🌐 Web Mode (`web_app.py`)
- Browser-based interface
- Access from any device on network
- Real-time video streaming via Socket.IO
- ~15 FPS (optimized for web)

#### 🖥️ Hybrid Mode (`hybrid_detector.py`)
- **PC Mode**: High-performance OpenCV window (~30 FPS)
- **Web Mode**: Browser dashboard for monitoring
- Best of both worlds
- Clean video feed without overlays

#### 💻 Classic Mode (`DrowsinessDetector_Universal.py`)
- PyQt5 desktop GUI
- Original implementation
- Full-featured interface

### Performance

- **Docker**: ~20-25 FPS (CPU mode)
- **Native GPU**: ~30 FPS (RTX 3070 Ti)
- **Native CPU**: ~10-15 FPS (compatible fallback)
- **Web Streaming**: ~15 FPS (optimized for bandwidth)

## ⚙️ Configuration

Edit `telegram_config.json`:
```json
{
  "bot_token": "your_bot_token_here",
  "chat_id": "your_chat_id_here", 
  "emergency_threshold": 4.0
}
```

## 🚨 Emergency Alerts

When microsleep duration exceeds threshold:
- 🔊 Immediate sound alert
- 📱 Telegram message with timestamp and severity
- 🚨 Visual warning in interface

## 📊 Monitoring

The interface displays:
- **Blinks**: Total eye blink count
- **Microsleeps**: Duration of eyes closed (seconds)
- **Yawns**: Total yawn count  
- **Yawn Duration**: Current yawn length
- **FPS**: Processing speed
- **Device**: GPU/CPU mode
- **Alerts**: Emergency notification status

## 🔧 Troubleshooting

**GPU Issues:**
- Run `launch.bat` and select "Fix GPU setup"
- Or use CPU mode for immediate compatibility

**Camera Issues:**
- Ensure webcam is connected and not used by other apps
- Check camera permissions in Windows settings

**Telegram Issues:**
- Verify bot token and chat ID are correct
- Ensure internet connection is stable
- Check that you've sent at least one message to your bot

## 🎯 Model Training

The models were trained on:
- **Eye Dataset**: ~53,000 images (open/closed eyes)
- **Yawn Dataset**: Custom yawning detection data
- **Auto-labeling**: GroundingDINO for bounding box generation

## 🚀 Performance Tips

- Use GPU mode for best performance
- Ensure good lighting for accurate detection
- Position camera at eye level
- Minimize background distractions
