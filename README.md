# Drowsiness Detection System

Real-time drowsiness detection using computer vision and machine learning to monitor driver alertness and prevent accidents.

## 🚀 Quick Start

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
├── DrowsinessDetector_Universal.py  # Main detection system
├── setup_telegram.py               # Telegram bot setup
├── telegram_config.json           # Telegram configuration
├── launch.bat                     # Easy launcher
├── requirements.txt              # Dependencies
├── dataset.yaml                 # YOLO dataset config
└── runs/                       # Trained models
    ├── detecteye/
    └── detectyawn/
```

## ✨ Features

- **Real-time Detection**: Monitors eye closure and yawning via webcam
- **GPU Acceleration**: Optimized for NVIDIA RTX GPUs (falls back to CPU)
- **Telegram Alerts**: Emergency notifications when critical drowsiness detected
- **Smart Thresholds**: Configurable microsleep detection (default: 4 seconds)
- **Visual Interface**: PyQt5 GUI with real-time statistics
- **Sound Alerts**: Audio warnings for immediate attention

## 🔧 Installation

### Option 1: Quick Setup (Recommended)
```cmd
# Clone repository
git clone https://github.com/tyrerodr/Real_time_drowsy_driving_detection.git
cd Real_time_drowsy_driving_detection

# Run launcher - it will guide you through setup
launch.bat
```

### Option 2: Manual Setup
```cmd
# Create virtual environment
python -m venv venv_gpu
venv_gpu\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Run detection
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

The system uses two YOLOv8 models:

1. **Eye Detection**: Classifies eyes as open/closed
2. **Yawn Detection**: Detects mouth open (yawning) vs closed

**Detection Logic:**
- Tracks blinks and microsleep duration
- Monitors yawn frequency and duration  
- Triggers alerts when thresholds exceeded
- Sends Telegram notifications for emergencies

**Performance:**
- GPU Mode: ~30 FPS (RTX 3070 Ti)
- CPU Mode: ~10-15 FPS (compatible fallback)

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

## 📝 License

This project is for educational and safety purposes. Use responsibly.

---

**Eng. Tyrone Eduardo Rodriguez Motato**  
Computer Vision Engineer  
Guayaquil, Ecuador  
Email: tyrerodr@hotmail.com