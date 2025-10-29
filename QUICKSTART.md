# 🚀 Quick Start Guide

## What You Have Now

✅ **Cloud Dashboard** - Centralized monitoring on EC2  
✅ **Local Detection** - YOLO models run on your computer  
✅ **Docker Support** - Easy deployment  
✅ **Multi-Device** - Monitor multiple computers from one dashboard  

## 🎯 Next Steps

### Option 1: Deploy to EC2 (Recommended for Cloud Dashboard)

#### Step 1: Connect to Your EC2
```bash
chmod 400 "linuxdevops.pem"
ssh -i "linuxdevops.pem" ubuntu@ec2-13-221-227-218.compute-1.amazonaws.com
```

#### Step 2: Clone Repository on EC2
```bash
git clone https://github.com/vedraut00/real_time_drowsiness_locations.git
cd real_time_drowsiness_locations
```

#### Step 3: Run Deployment Script
```bash
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

#### Step 4: Copy Files
```bash
cp cloud_dashboard.py ~/drowsiness-cloud/
cp -r templates ~/drowsiness-cloud/
```

#### Step 5: Generate API Key
```bash
cd ~/drowsiness-cloud
python3 -c "import secrets; print(secrets.token_hex(32))"
# Save this key - you'll need it!
```

#### Step 6: Start Service
```bash
# Set API key
export DEVICE_API_KEY="your_generated_key"
echo 'export DEVICE_API_KEY="your_generated_key"' >> ~/.bashrc

# Start service
sudo systemctl start drowsiness-cloud
sudo systemctl enable drowsiness-cloud
sudo systemctl status drowsiness-cloud
```

#### Step 7: Configure AWS Security Group
1. Go to AWS Console → EC2 → Security Groups
2. Add Inbound Rule:
   - Type: Custom TCP
   - Port: 5000
   - Source: 0.0.0.0/0

#### Step 8: Access Dashboard
Open browser: `http://ec2-13-221-227-218.compute-1.amazonaws.com:5000`

**Login:**
- Username: `admin`
- Password: `admin123` (change this!)

---

### Option 2: Run Locally with Docker (Easiest)

#### Windows
```bash
docker-run.bat
```

#### Linux/Mac
```bash
chmod +x docker-run.sh
./docker-run.sh
```

Access at: `http://localhost:5000`

---

### Option 3: Run Native (Advanced)

```bash
# Install dependencies
pip install -r requirements.txt

# Run hybrid mode (best option)
python hybrid_detector.py

# Or web mode
python web_app.py
```

---

## 🔗 Connect Local Computer to Cloud

### Step 1: Create cloud_config.json
```json
{
  "cloud_url": "http://ec2-13-221-227-218.compute-1.amazonaws.com:5000",
  "api_key": "your_api_key_from_ec2",
  "device_name": "My-Laptop",
  "enabled": true
}
```

### Step 2: Run Detection
```bash
python hybrid_detector.py
```

Your computer will now send data to the cloud dashboard!

---

## 📊 What Each Mode Does

### 🌐 Cloud Dashboard (EC2)
- **Purpose:** Centralized monitoring
- **Runs on:** EC2 instance
- **Access:** Web browser from anywhere
- **Features:**
  - User authentication
  - Multi-device monitoring
  - Real-time alerts
  - Location tracking
  - Alert history

### 💻 Local Detection (Your Computer)
- **Purpose:** Run YOLO models and camera
- **Runs on:** Your computer
- **Features:**
  - Real-time drowsiness detection
  - Local web interface
  - Sends data to cloud
  - Works offline if cloud unavailable

### 🐳 Docker Mode
- **Purpose:** Easy deployment
- **Runs on:** Any computer with Docker
- **Features:**
  - No Python installation needed
  - Isolated environment
  - Easy updates

---

## 🎮 Usage Scenarios

### Scenario 1: Single User
1. Run Docker locally: `docker-run.bat`
2. Access: `http://localhost:5000`
3. No cloud needed

### Scenario 2: Multiple Computers, One Dashboard
1. Deploy cloud dashboard to EC2
2. On each computer:
   - Create `cloud_config.json`
   - Run `python hybrid_detector.py`
3. Monitor all from cloud dashboard

### Scenario 3: Fleet Management
1. Deploy cloud dashboard to EC2
2. Create user accounts for each driver
3. Each vehicle runs detection locally
4. Fleet manager monitors from dashboard

---

## 🔧 Troubleshooting

### EC2 Not Accessible
```bash
# Check service
sudo systemctl status drowsiness-cloud

# Check logs
sudo journalctl -u drowsiness-cloud -f

# Check firewall
sudo ufw status

# Check AWS Security Group in console
```

### Local Can't Connect to Cloud
```bash
# Test connection
curl http://ec2-13-221-227-218.compute-1.amazonaws.com:5000/api/dashboard/data

# Check cloud_config.json
cat cloud_config.json

# Verify API key matches EC2
```

### Docker Issues
```bash
# Check Docker is running
docker info

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

---

## 📚 Documentation

- **Full Cloud Setup:** [CLOUD_SETUP.md](CLOUD_SETUP.md)
- **Docker Guide:** [DOCKER_README.md](DOCKER_README.md)
- **Main README:** [README.md](README.md)

---

## 🎯 Recommended Setup

**For Testing:**
```bash
docker-run.bat  # Easiest way to test
```

**For Production:**
1. Deploy cloud dashboard to EC2
2. Run local detection on each computer
3. Monitor from cloud dashboard
4. Set up HTTPS with Let's Encrypt
5. Configure backups

---

## 🆘 Need Help?

1. Check logs: `sudo journalctl -u drowsiness-cloud -f`
2. Test connection: `curl http://your-ec2-ip:5000`
3. Verify API key in both places
4. Check AWS Security Group settings
5. Review [CLOUD_SETUP.md](CLOUD_SETUP.md)

---

## 🎉 You're All Set!

Your drowsiness detection system is now:
- ✅ Containerized with Docker
- ✅ Cloud-enabled with EC2
- ✅ Multi-device ready
- ✅ Production-ready

**Next:** Follow the steps above to deploy!
