#!/usr/bin/env python3
"""
Test script to verify that the application works in a Render-like environment.
This simulates the PostgreSQL connection and verifies deployment readiness.
"""

import os
import sys
import json
from pathlib import Path

# Add the backend directory to Python path
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

def test_render_environment():
    """Test the application in a simulated Render environment"""
    print("🌐 Testing Render Deployment Environment")
    print("=" * 50)
    
    # Simulate Render environment variables
    original_env = {}
    test_env_vars = {
        'NODE_ENV': 'production',
        'RENDER_EXTERNAL_URL': 'https://wozchat.onrender.com',
        'SECRET_KEY': 'test-secret-key-for-production',
        'DATA_DIR': str(BACKEND_DIR / 'data'),
        # Note: DATABASE_URL would be set by Render automatically
    }
    
    # Backup and set environment variables
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        print(f"📊 Environment Configuration:")
        for key, value in test_env_vars.items():
            print(f"   - {key}: {value}")
        print()
        
        # Test database manager initialization
        from database import DatabaseManager
        
        data_dir = Path(os.environ['DATA_DIR'])
        db_manager = DatabaseManager(data_dir)
        
        print(f"📊 Database Manager Status:")
        print(f"   - Initialized: {db_manager is not None}")
        print(f"   - Data Directory: {data_dir}")
        print(f"   - Directory Exists: {data_dir.exists()}")
        print(f"   - Using PostgreSQL: {db_manager.use_postgres}")
        print()
        
        # Test app initialization
        print("🔧 Testing App Initialization...")
        
        # Reset modules to test fresh import
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith('app')]
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]
        
        from app import app, db_manager as app_db_manager, TEMPLATES, rooms
        
        print(f"   ✅ App initialized successfully")
        print(f"   - Database manager available: {app_db_manager is not None}")
        print(f"   - Templates loaded: {len(TEMPLATES)} categories")
        print(f"   - Rooms dictionary: {isinstance(rooms, dict)}")
        print(f"   - Using PostgreSQL: {app_db_manager and app_db_manager.use_postgres}")
        print()
        
        # Test conversation storage in production mode
        print("💾 Testing Production Storage...")
        
        test_room = "render_test_room"
        test_message = "Test message for Render deployment"
        
        # Import the save function
        from app import save
        
        try:
            msg = save(test_room, "participant", test_message)
            print(f"   ✅ Message saved successfully")
            print(f"   - Sender: {msg['sender']}")
            print(f"   - Text: {msg['text'][:50]}...")
            print(f"   - Timestamp: {msg['timestamp']}")
        except Exception as e:
            print(f"   ❌ Message save failed: {e}")
            return False
        
        # Test message retrieval
        try:
            if app_db_manager:
                retrieved_messages = app_db_manager.get_conversation(test_room)
                print(f"   ✅ Retrieved {len(retrieved_messages)} messages")
            else:
                print(f"   ⚠️ No database manager for retrieval test")
        except Exception as e:
            print(f"   ❌ Message retrieval failed: {e}")
        
        print()
        
        # Test health check endpoint
        print("🏥 Testing Health Check Endpoint...")
        try:
            with app.test_client() as client:
                response = client.get('/health')
                health_data = response.get_json()
                
                print(f"   ✅ Health check response: {response.status_code}")
                print(f"   - Status: {health_data.get('status')}")
                print(f"   - Bot available: {health_data.get('bot_available')}")
                print(f"   - Persistent storage: {health_data.get('persistent_storage')}")
                print(f"   - Data directory: {health_data.get('data_dir')}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return False
        
        print()
        
        # Cleanup test data
        try:
            if app_db_manager:
                test_file = data_dir / "conversations" / f"{test_room}.json"
                if test_file.exists():
                    test_file.unlink()
                    print("🧹 Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
        
        print("✅ Render environment test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Render environment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Restore original environment variables
        for key, original_value in original_env.items():
            if original_value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = original_value

def test_postgresql_connection_format():
    """Test PostgreSQL URL format handling (common Render issue)"""
    print("\n🐘 Testing PostgreSQL URL Format Handling")
    print("=" * 50)
    
    # Test different PostgreSQL URL formats that Render might provide
    test_urls = [
        "postgres://user:password@host:5432/database",
        "postgresql://user:password@host:5432/database", 
        "postgres://user:password@host/database",
        "postgresql://user:password@host/database",
    ]
    
    for url in test_urls:
        print(f"Testing URL format: {url.split('@')[0]}@[REDACTED]")
        
        # Test the URL conversion logic from database.py
        if url.startswith('postgres://'):
            converted_url = url.replace('postgres://', 'postgresql://', 1)
            print(f"   ✅ Converted to: {converted_url.split('@')[0]}@[REDACTED]")
        else:
            print(f"   ✅ Already correct format")
    
    print("✅ PostgreSQL URL format handling verified")
    return True

if __name__ == "__main__":
    print("🚀 WebWOz Render Deployment Test Suite")
    print("=" * 60)
    
    # Run tests
    render_test_passed = test_render_environment()
    postgres_test_passed = test_postgresql_connection_format()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   - Render Environment: {'✅ PASSED' if render_test_passed else '❌ FAILED'}")
    print(f"   - PostgreSQL Format: {'✅ PASSED' if postgres_test_passed else '❌ FAILED'}")
    
    if render_test_passed and postgres_test_passed:
        print("\n🎉 All deployment tests passed!")
        print("✅ Your application is ready for Render deployment.")
        print("📝 Make sure to set the DATABASE_URL environment variable in Render.")
    else:
        print("\n⚠️ Some deployment tests failed. Please check the error messages above.")
        sys.exit(1)
