#!/bin/bash

echo "========================================="
echo " Drowsiness Detection - EC2 Deployment"
echo "========================================="
echo ""

# Update system
echo "[1/6] Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and dependencies
echo "[2/6] Installing Python and dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv

# Create application directory
echo "[3/6] Setting up application..."
mkdir -p ~/drowsiness-cloud
cd ~/drowsiness-cloud

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "[4/6] Installing Python packages..."
pip install --upgrade pip
pip install Flask==3.0.0 flask-socketio==5.3.5 python-socketio==5.10.0 requests==2.31.0

# Create systemd service
echo "[5/6] Creating systemd service..."
sudo tee /etc/systemd/system/drowsiness-cloud.service > /dev/null <<EOF
[Unit]
Description=Drowsiness Detection Cloud Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/drowsiness-cloud
Environment="PATH=$HOME/drowsiness-cloud/venv/bin"
Environment="DEVICE_API_KEY=change_this_api_key_in_production"
ExecStart=$HOME/drowsiness-cloud/venv/bin/python cloud_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
echo "[6/6] Configuring firewall..."
sudo ufw allow 5000/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

echo ""
echo "========================================="
echo " Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Copy cloud_dashboard.py to ~/drowsiness-cloud/"
echo "2. Copy templates/ folder to ~/drowsiness-cloud/"
echo "3. Start service: sudo systemctl start drowsiness-cloud"
echo "4. Enable on boot: sudo systemctl enable drowsiness-cloud"
echo "5. Check status: sudo systemctl status drowsiness-cloud"
echo "6. View logs: sudo journalctl -u drowsiness-cloud -f"
echo ""
echo "Access dashboard at: http://YOUR_EC2_IP:5000"
echo "Default login: admin / admin123"
echo ""
echo "⚠️  IMPORTANT: Change default password and API key!"
echo ""
