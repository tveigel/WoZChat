#!/usr/bin/env python3
"""
Simple script to verify deployment health.
Usage: python verify_deployment.py https://wozchat.onrender.com
"""

import sys
import requests
import json

def verify_deployment(base_url):
    """Verify that the deployment is working correctly."""
    print(f"🔍 Verifying deployment at {base_url}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed:")
            for key, value in health_data.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test main endpoints
    endpoints_to_test = [
        ("/", "Root redirect"),
        ("/wizard", "Wizard interface"),
        ("/api/new_room", "Room creation API")
    ]
    
    for endpoint, description in endpoints_to_test:
        try:
            if endpoint == "/api/new_room":
                response = requests.post(f"{base_url}{endpoint}", timeout=10)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code in [200, 302]:  # 302 for redirects
                print(f"✅ {description}: OK")
            else:
                print(f"⚠️ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
    
    print("🎉 Deployment verification complete!")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_deployment.py <base_url>")
        print("Example: python verify_deployment.py https://wozchat.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    verify_deployment(base_url)
