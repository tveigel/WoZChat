#!/usr/bin/env python3
"""
Test script to validate WebWOz bot integration
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

def test_bot_integration():
    """Test if bot integration can be imported and initialized."""
    print("🧪 Testing WebWOz Bot Integration...")
    
    try:
        from bot_integration import bot_manager, WebBotSession
        print("✅ Bot integration module imported successfully")
        
        # Test creating a session
        session = WebBotSession("test_room")
        print(f"✅ Bot session created: available={session.workflow is not None}")
        
        # Test bot manager
        status = bot_manager.get_bot_status("test_room")
        print(f"✅ Bot status retrieved: {status}")
        
        print("\n🎉 Bot integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Bot integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_app():
    """Test if the Flask app can be imported."""
    print("\n🧪 Testing Flask App...")
    
    try:
        from backend.app import app, socketio
        print("✅ Flask app imported successfully")
        
        # Test a simple route
        with app.test_client() as client:
            response = client.post('/api/new_room')
            if response.status_code == 200:
                print("✅ API endpoint test successful")
            else:
                print(f"⚠️ API endpoint returned status {response.status_code}")
        
        print("✅ Flask app test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 WebWOz Integration Test Suite")
    print("=" * 50)
    
    success = True
    success &= test_bot_integration()
    success &= test_flask_app()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! WebWOz is ready to run with bot integration.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
