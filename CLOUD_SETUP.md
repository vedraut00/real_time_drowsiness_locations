# ☁️ Cloud Dashboard Setup Guide

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐
│  Local Computer │────────▶│   EC2 Instance   │
│  (Detection)    │  HTTPS  │  (Dashboard)     │
│  - YOLO Models  │         │  - Authentication│
│  - Camera       │         │  - Visualization │
│  - Processing   │         │  - Data Storage  │
└─────────────────┘         └──────────────────┘
        │                            │
        │                            ▼
        │                    ┌──────────────┐
        └───────────────────▶│   Browser    │
                             │  (Monitor)   │
                             └──────────────┘
```

## Part 1: EC2 Instance Setup

### Step 1: Connect to EC2

```bash
# Make key file secure
chmod 400 "linuxdevops.pem"

# Connect to EC2
ssh -i "linuxdevops.pem" ubuntu@ec2-13-221-227-218.compute-1.amazonaws.com
```

### Step 2: Deploy Cloud Dashboard

```bash
# Download deployment script
wget https://raw.githubusercontent.com/vedraut00/real_time_drowsiness_locations/main/deploy_ec2.sh

# Make executable
chmod +x deploy_ec2.sh

# Run deployment
./deploy_ec2.sh
```

### Step 3: Upload Application Files

From your local computer:

```bash
# Upload cloud dashboard
scp -i "linuxdevops.pem" cloud_dashboard.py ubuntu@ec2-13-221-227-218.compute-1.amazonaws.com:~/drowsiness-cloud/

# Upload templates folder
scp -i "linuxdevops.pem" -r templates/ ubuntu@ec2-13-221-227-218.compute-1.amazonaws.com:~/drowsiness-cloud/
```

### Step 4: Configure Security

On EC2:

```bash
cd ~/drowsiness-cloud

# Generate secure API key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Save the API key - you'll need it for local clients
# Example: a1b2c3d4e5f6...

# Set environment variable
echo 'export DEVICE_API_KEY="your_generated_api_key"' >> ~/.bashrc
source ~/.bashrc
```

### Step 5: Start Service

```bash
# Start the service
sudo systemctl start drowsiness-cloud

# Enable on boot
sudo systemctl enable drowsiness-cloud

# Check status
sudo systemctl status drowsiness-cloud

# View logs
sudo journalctl -u drowsiness-cloud -f
```

### Step 6: Configure AWS Security Group

In AWS Console:
1. Go to EC2 → Security Groups
2. Select your instance's security group
3. Add Inbound Rules:
   - Type: Custom TCP
   - Port: 5000
   - Source: 0.0.0.0/0 (or your IP for security)
   - Description: Cloud Dashboard

## Part 2: Local Computer Setup

### Step 1: Configure Cloud Connection

Create `cloud_config.json`:

```json
{
  "cloud_url": "http://ec2-13-221-227-218.compute-1.amazonaws.com:5000",
  "api_key": "your_generated_api_key_from_ec2",
  "device_name": "My-Computer",
  "enabled": true,
  "send_stats_interval": 5,
  "send_alerts": true
}
```

### Step 2: Update Hybrid Detector

The hybrid detector will automatically detect `cloud_config.json` and connect to the cloud.

### Step 3: Run Detection

```bash
# Windows
python hybrid_detector.py

# Or use the launcher
start_hybrid.bat
```

## Part 3: Access Dashboard

### Web Interface

Open browser and navigate to:
```
http://ec2-13-221-227-218.compute-1.amazonaws.com:5000
```

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT:** Change the default password immediately!

### Features

1. **Real-time Monitoring**
   - View all connected devices
   - Live status updates
   - Device statistics

2. **Alert Management**
   - Real-time drowsiness alerts
   - Alert history
   - Severity levels

3. **Location Tracking**
   - Interactive map
   - Device locations
   - Alert locations

4. **User Management**
   - Multi-user support
   - Role-based access
   - Secure authentication

## Part 4: Multiple Devices

### Add More Devices

On each computer:

1. Install the drowsiness detection system
2. Create `cloud_config.json` with the same cloud URL and API key
3. Set unique `device_name` for each device
4. Run the detection system

All devices will appear in the cloud dashboard!

## Troubleshooting

### EC2 Connection Issues

```bash
# Check if service is running
sudo systemctl status drowsiness-cloud

# Check logs
sudo journalctl -u drowsiness-cloud -n 50

# Restart service
sudo systemctl restart drowsiness-cloud

# Check port
sudo netstat -tulpn | grep 5000
```

### Local Client Issues

```bash
# Test connection
curl http://ec2-13-221-227-218.compute-1.amazonaws.com:5000/api/dashboard/data

# Check cloud_config.json
cat cloud_config.json

# Test with Python
python local_client.py
```

### Firewall Issues

```bash
# On EC2
sudo ufw status
sudo ufw allow 5000/tcp

# Check AWS Security Group in console
```

## Production Recommendations

### 1. Use HTTPS

Install Let's Encrypt SSL:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 2. Use Database

Replace in-memory storage with PostgreSQL or MongoDB:

```bash
sudo apt-get install postgresql
pip install psycopg2-binary
```

### 3. Set Up Monitoring

```bash
# Install monitoring tools
sudo apt-get install htop iotop

# Set up log rotation
sudo nano /etc/logrotate.d/drowsiness-cloud
```

### 4. Backup Configuration

```bash
# Backup users and data
cd ~/drowsiness-cloud
tar -czf backup-$(date +%Y%m%d).tar.gz users.json *.log

# Copy to S3 (optional)
aws s3 cp backup-*.tar.gz s3://your-bucket/backups/
```

### 5. Update Application

```bash
# Pull latest code
cd ~/drowsiness-cloud
git pull

# Restart service
sudo systemctl restart drowsiness-cloud
```

## API Endpoints

### Device Registration
```
POST /api/device/register
Body: {
  "device_id": "unique_id",
  "device_name": "My Device",
  "api_key": "your_api_key"
}
```

### Send Alert
```
POST /api/device/alert
Body: {
  "device_id": "unique_id",
  "duration": 3.5,
  "location": {"lat": 40.7128, "lng": -74.0060, "address": "NYC"}
}
```

### Send Statistics
```
POST /api/device/stats
Body: {
  "device_id": "unique_id",
  "stats": {
    "blink_count": 150,
    "yawn_count": 5,
    "fps": 28
  }
}
```

## Cost Estimation

### AWS t2.micro (Free Tier)
- **Instance**: Free for 12 months
- **Storage**: 30 GB free
- **Data Transfer**: 15 GB/month free
- **After Free Tier**: ~$8-10/month

### Scaling
- **t2.small**: ~$17/month (recommended for 10+ devices)
- **t2.medium**: ~$34/month (recommended for 50+ devices)

## Support

For issues or questions:
- GitHub: https://github.com/vedraut00/real_time_drowsiness_locations
- Check logs: `sudo journalctl -u drowsiness-cloud -f`
- EC2 Status: `sudo systemctl status drowsiness-cloud`
