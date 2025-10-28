#!/usr/bin/env python3
"""
Test script to verify which interface is being served
"""

import requests
import time

def test_interface():
    try:
        print("🧪 Testing interface at http://localhost:5000...")
        
        response = requests.get('http://localhost:5000', timeout=5)
        
        if response.status_code == 200:
            content = response.text
            
            print(f"✅ Server is running (Status: {response.status_code})")
            print(f"📄 Content length: {len(content)} characters")
            
            # Check for hybrid interface elements
            if "Choose Detection Mode" in content:
                print("✅ Hybrid interface detected!")
                
                if "PC Mode (Recommended)" in content:
                    print("✅ PC Mode option found")
                else:
                    print("❌ PC Mode option missing")
                    
                if "Web Mode" in content:
                    print("✅ Web Mode option found")
                else:
                    print("❌ Web Mode option missing")
                    
                if "startPCMode()" in content:
                    print("✅ PC Mode JavaScript function found")
                else:
                    print("❌ PC Mode JavaScript function missing")
                    
                if "startWebMode()" in content:
                    print("✅ Web Mode JavaScript function found")
                else:
                    print("❌ Web Mode JavaScript function missing")
                    
            elif "Drowsiness Detection Dashboard" in content:
                print("⚠️ Regular web app interface detected (not hybrid)")
                
            else:
                print("❓ Unknown interface type")
                
            # Check admin link
            if "/admin" in content:
                print("✅ Admin panel link found")
            else:
                print("❌ Admin panel link missing")
                
        else:
            print(f"❌ Server error (Status: {response.status_code})")
            
    except requests.exceptions.ConnectionError:
        print("❌ No server running at http://localhost:5000")
        print("💡 Start the server with: python hybrid_detector.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_interface()