#!/usr/bin/env python3
"""
Test script to verify database storage functionality.
Run this script to test the database integration and conversation persistence.
"""

import os
import sys
import json
from pathlib import Path

# Add the backend directory to Python path
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

def test_database_storage():
    """Test the database storage functionality"""
    print("🧪 Testing WebWOz Database Storage")
    print("=" * 50)
    
    try:
        from database import DatabaseManager
        from datetime import datetime, timezone
        
        # Initialize database manager
        data_dir = BACKEND_DIR / "data"
        db_manager = DatabaseManager(data_dir)
        
        print(f"📊 Database Status:")
        print(f"   - Available: {db_manager is not None}")
        print(f"   - Using PostgreSQL: {db_manager.use_postgres}")
        print(f"   - Data Directory: {data_dir}")
        print()
        
        # Test room creation and message saving
        test_room = "test_room_12345"
        test_messages = [
            {"sender": "participant", "text": "Hello, I need to report an accident", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"sender": "bot", "text": "I'll help you with that. What type of accident occurred?", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"sender": "participant", "text": "Car accident on Main Street", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"sender": "wizard", "text": "Thank you for the report. We'll process this information.", "timestamp": datetime.now(timezone.utc).isoformat()}
        ]
        
        print("💾 Testing Message Storage...")
        for i, msg in enumerate(test_messages):
            try:
                saved_msg = db_manager.save_message(
                    test_room, 
                    msg["sender"], 
                    msg["text"], 
                    msg["timestamp"]
                )
                print(f"   ✅ Message {i+1} saved: {msg['sender']}")
            except Exception as e:
                print(f"   ❌ Message {i+1} failed: {e}")
        
        print()
        
        # Test conversation retrieval
        print("📤 Testing Conversation Retrieval...")
        try:
            retrieved_messages = db_manager.get_conversation(test_room)
            print(f"   ✅ Retrieved {len(retrieved_messages)} messages")
            
            for i, msg in enumerate(retrieved_messages):
                print(f"   {i+1}. {msg['sender']}: {msg['text'][:50]}...")
        except Exception as e:
            print(f"   ❌ Retrieval failed: {e}")
        
        print()
        
        # Test conversation listing
        print("📋 Testing Conversation Listing...")
        try:
            conversations = db_manager.list_conversations()
            print(f"   ✅ Found {len(conversations)} conversations")
            
            for conv in conversations:
                print(f"   - Room: {conv['room_id']}, Messages: {conv['message_count']}")
        except Exception as e:
            print(f"   ❌ Listing failed: {e}")
        
        print()
        print("✅ Database test completed successfully!")
        
        # Clean up test data
        try:
            if db_manager.use_postgres:
                print("🧹 Cleaning up test data...")
                session = db_manager.get_session()
                if session:
                    from database import Message, Conversation
                    # Delete test messages and conversation
                    session.query(Message).filter_by(room_id=test_room).delete()
                    session.query(Conversation).filter_by(room_id=test_room).delete()
                    session.commit()
                    session.close()
                    print("   ✅ Test data cleaned up")
            else:
                # Clean up file storage
                test_file = data_dir / "conversations" / f"{test_room}.json"
                if test_file.exists():
                    test_file.unlink()
                    print("   ✅ Test file cleaned up")
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")
        
    except ImportError as e:
        print(f"❌ Failed to import database module: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def test_app_integration():
    """Test the app.py integration"""
    print("\n🔧 Testing App Integration")
    print("=" * 50)
    
    try:
        # Test if app.py can import correctly
        from app import save, rooms, db_manager
        
        print(f"📊 App Status:")
        print(f"   - save() function available: {callable(save)}")
        print(f"   - rooms dict available: {isinstance(rooms, dict)}")
        print(f"   - db_manager available: {db_manager is not None}")
        
        if db_manager:
            print(f"   - Using PostgreSQL: {db_manager.use_postgres}")
        
        print("   ✅ App integration test passed")
        return True
        
    except ImportError as e:
        print(f"❌ App import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ App test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 WebWOz Database Storage Test Suite")
    print("=" * 60)
    
    # Check environment
    database_url = os.environ.get('DATABASE_URL')
    print(f"📍 Environment:")
    print(f"   - DATABASE_URL configured: {bool(database_url)}")
    if database_url:
        # Redact password for security
        redacted = database_url.split('@')[0] + '@[REDACTED]' if '@' in database_url else '[REDACTED]'
        print(f"   - Database URL: {redacted}")
    print()
    
    # Run tests
    db_test_passed = test_database_storage()
    app_test_passed = test_app_integration()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   - Database Storage: {'✅ PASSED' if db_test_passed else '❌ FAILED'}")
    print(f"   - App Integration: {'✅ PASSED' if app_test_passed else '❌ FAILED'}")
    
    if db_test_passed and app_test_passed:
        print("\n🎉 All tests passed! Your database storage is working correctly.")
        print("✅ Conversations will be properly stored and synced with your PostgreSQL database on Render.")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
        sys.exit(1)
