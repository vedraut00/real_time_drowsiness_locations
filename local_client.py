#!/usr/bin/env python3
"""
Local Client - Runs on user's computer
Sends data to cloud dashboard while running detection locally
"""

import requests
import threading
import time
import json
import uuid
import socket
import hashlib
import os
from datetime import datetime

class CloudClient:
    def __init__(self, cloud_url, api_key, device_name=None):
        """
        Initialize cloud client
        
        Args:
            cloud_url: URL of cloud dashboard (e.g., http://ec2-13-221-227-218.compute-1.amazonaws.com:5000)
            api_key: API key for authentication
            device_name: Optional device name
        """
        self.cloud_url = cloud_url.rstrip('/')
        self.api_key = api_key
        self.device_id = self.get_device_id()
        self.device_name = device_name or f"{socket.gethostname()}-{self.device_id[:8]}"
        self.connected = False
        self.heartbeat_interval = 30  # seconds
        self.stats_interval = 5  # seconds
        
        # Register device
        self.register_device()
        
        # Start background threads
        self.start_heartbeat()
    
    def get_device_id(self):
        """Generate unique device ID"""
        # Use MAC address for consistent ID
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                       for elements in range(0,2*6,2)][::-1])
        return hashlib.sha256(mac.encode()).hexdigest()
    
    def register_device(self):
        """Register device with cloud"""
        try:
            response = requests.post(
                f"{self.cloud_url}/api/device/register",
                json={
                    "device_id": self.device_id,
                    "device_name": self.device_name,
                    "api_key": self.api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.connected = True
                print(f"✅ Device registered: {self.device_name}")
                print(f"📱 Device ID: {self.device_id}")
            else:
                print(f"❌ Registration failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("⚠️  Running in offline mode")
    
    def send_heartbeat(self):
        """Send heartbeat to cloud"""
        while True:
            try:
                if self.connected:
                    response = requests.post(
                        f"{self.cloud_url}/api/device/heartbeat",
                        json={"device_id": self.device_id},
                        timeout=5
                    )
                    
                    if response.status_code != 200:
                        print(f"⚠️  Heartbeat failed: {response.status_code}")
                        
            except Exception as e:
                print(f"⚠️  Heartbeat error: {e}")
            
            time.sleep(self.heartbeat_interval)
    
    def start_heartbeat(self):
        """Start heartbeat thread"""
        thread = threading.Thread(target=self.send_heartbeat, daemon=True)
        thread.start()
    
    def send_alert(self, duration, location=None):
        """Send drowsiness alert to cloud"""
        if not self.connected:
            return False
        
        try:
            alert_data = {
                "device_id": self.device_id,
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "location": location or {"lat": 0, "lng": 0, "address": "Unknown"}
            }
            
            response = requests.post(
                f"{self.cloud_url}/api/device/alert",
                json=alert_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"📤 Alert sent to cloud: {duration:.1f}s")
                return True
            else:
                print(f"❌ Alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Alert error: {e}")
            return False
    
    def send_stats(self, stats, location=None):
        """Send statistics to cloud"""
        if not self.connected:
            return False
        
        try:
            stats_data = {
                "device_id": self.device_id,
                "stats": stats,
                "location": location or {"lat": 0, "lng": 0, "address": "Unknown"}
            }
            
            response = requests.post(
                f"{self.cloud_url}/api/device/stats",
                json=stats_data,
                timeout=5
            )
            
            return response.status_code == 200
                
        except Exception as e:
            # Silent fail for stats (non-critical)
            return False

import hashlib

def load_cloud_config():
    """Load cloud configuration"""
    config_file = 'cloud_config.json'
    default_config = {
        "cloud_url": "http://localhost:5000",
        "api_key": "default_key_change_me",
        "device_name": socket.gethostname(),
        "enabled": False
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

import os

# Example usage
if __name__ == '__main__':
    config = load_cloud_config()
    
    if config['enabled']:
        client = CloudClient(
            cloud_url=config['cloud_url'],
            api_key=config['api_key'],
            device_name=config['device_name']
        )
        
        print("✅ Cloud client initialized")
        print("📊 Sending test data...")
        
        # Test alert
        client.send_alert(3.5, {"lat": 40.7128, "lng": -74.0060, "address": "New York, NY"})
        
        # Test stats
        client.send_stats({
            "blink_count": 150,
            "yawn_count": 5,
            "continuous_sleep": 0.5,
            "fps": 28
        })
        
        print("✅ Test complete - check cloud dashboard")
        
        # Keep alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
    else:
        print("⚠️  Cloud integration disabled")
        print("📝 Edit cloud_config.json to enable")
