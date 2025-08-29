#!/usr/bin/env python3
"""Simple server health check script"""
import time
import requests
import sys

def check_server():
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print(f"✅ Server is running! Status: {response.status_code}")
                print(f"📊 Dashboard: http://localhost:8000/dashboard")
                print(f"📖 API Docs: http://localhost:8000/docs")
                print(f"🔗 Health: http://localhost:8000/health")
                return True
        except requests.exceptions.ConnectionError:
            print(f"⏳ Attempt {attempt + 1}/{max_attempts}: Server not ready yet...")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(2)
    
    print("❌ Server failed to start within 60 seconds")
    return False

if __name__ == "__main__":
    success = check_server()
    sys.exit(0 if success else 1)