#!/usr/bin/env python3
"""
Test script for persistent storage functionality.
Run this to verify that conversation persistence is working correctly.
"""

import json
import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"  # Change to your Render URL for production testing
TEST_ROOM_ID = None

def test_persistence():
    """Test the complete persistence workflow."""
    global TEST_ROOM_ID
    
    print("🧪 Testing WebWOz Persistent Storage")
    print("=" * 50)
    
    # 1. Check health status
    print("\n1. Checking health and storage status...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        health_data = response.json()
        print(f"   ✅ Service healthy: {health_data['status']}")
        print(f"   📁 Data directory exists: {health_data.get('data_dir_exists', False)}")
        print(f"   💬 Active conversations: {health_data.get('active_conversations', 0)}")
        print(f"   💾 Saved conversations: {health_data.get('saved_conversations', 0)}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    # 2. Create new room
    print("\n2. Creating new room...")
    try:
        response = requests.post(f"{BASE_URL}/api/new_room")
        room_data = response.json()
        TEST_ROOM_ID = room_data["room"]
        print(f"   ✅ Created room: {TEST_ROOM_ID}")
    except Exception as e:
        print(f"   ❌ Room creation failed: {e}")
        return False
    
    # 3. Test conversation stats (before adding messages)
    print("\n3. Getting initial conversation stats...")
    try:
        response = requests.get(f"{BASE_URL}/api/conversations/stats")
        stats = response.json()
        initial_count = stats["total_conversations"]
        print(f"   📊 Total conversations: {initial_count}")
        print(f"   📊 Total messages: {stats['total_messages']}")
    except Exception as e:
        print(f"   ❌ Stats request failed: {e}")
        return False
    
    # 4. Simulate conversation (requires WebSocket, so we'll check via API)
    print(f"\n4. Checking conversation persistence...")
    print("   ℹ️  To fully test, send messages through the web interface")
    print(f"   ℹ️  Then check: {BASE_URL}/api/conversations/{TEST_ROOM_ID}")
    
    # 5. List conversations
    print("\n5. Listing all conversations...")
    try:
        response = requests.get(f"{BASE_URL}/api/conversations")
        conversations = response.json()
        print(f"   📋 Found {len(conversations['conversations'])} conversations")
        for conv in conversations['conversations'][:3]:  # Show first 3
            print(f"      - Room {conv['room_id']}: {conv['message_count']} messages")
    except Exception as e:
        print(f"   ❌ Listing conversations failed: {e}")
        return False
    
    # 6. Test template persistence
    print("\n6. Testing template persistence...")
    try:
        # Create a test template
        test_template = {
            "category": "Test",
            "key": "test_persistence",
            "value": f"Test template created at {time.time()}"
        }
        
        response = requests.post(f"{BASE_URL}/api/templates/item", json=test_template)
        if response.status_code == 201:
            print(f"   ✅ Created test template")
        else:
            print(f"   ⚠️  Template might already exist or failed: {response.status_code}")
        
        # Verify templates are listed
        response = requests.get(f"{BASE_URL}/api/templates")
        templates = response.json()
        if "Test" in templates and "test_persistence" in templates["Test"]:
            print(f"   ✅ Template persistence verified")
        else:
            print(f"   ⚠️  Template not found in response")
            
    except Exception as e:
        print(f"   ❌ Template testing failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Persistence testing completed!")
    print(f"🔗 Test room URL: {BASE_URL}/chat/{TEST_ROOM_ID}")
    print(f"🔗 Wizard URL: {BASE_URL}/wizard/{TEST_ROOM_ID}")
    print("\n💡 Next steps:")
    print("   1. Open the URLs above in different browser tabs")
    print("   2. Send some messages between participant and wizard")
    print(f"   3. Check persistence: {BASE_URL}/api/conversations/{TEST_ROOM_ID}")
    print("   4. Restart the server and verify messages are still there")
    
    return True

if __name__ == "__main__":
    success = test_persistence()
    exit(0 if success else 1)
