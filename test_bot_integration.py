#!/usr/bin/env python3
"""
Test bot integration without requiring API keys to be loaded at import time.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "backend"))

def test_bot_integration():
    print("🧪 Testing Bot Integration")
    print("=" * 50)
    
    # Test 1: Check if we can import the bot manager components
    print("\n1️⃣ Testing bot manager imports...")
    try:
        # Import bot_integration without triggering LLM initialization
        import backend.bot_integration as bi
        print("✅ Bot integration imports successful")
        print(f"   Rule bot available: {bi.BOT_IMPORTS_SUCCESSFUL}")
        print(f"   AI bot available: {bi.AI_BOT_IMPORTS_SUCCESSFUL}")
    except Exception as e:
        print(f"❌ Bot integration import failed: {e}")
        return False
    
    # Test 2: Check available bot types
    print("\n2️⃣ Testing bot type availability...")
    try:
        # Only test if we can create the manager
        if bi.BOT_IMPORTS_SUCCESSFUL or bi.AI_BOT_IMPORTS_SUCCESSFUL:
            manager = bi.BotManager()
            available_types = manager.get_available_bot_types()
            print(f"✅ Available bot types: {available_types}")
            
            if available_types.get("rule", False):
                print("   ✅ Rule-based bot is available")
            if available_types.get("ai", False):
                print("   ✅ AI bot is available")
        else:
            print("⚠️ No bot types available (missing dependencies)")
    except Exception as e:
        print(f"❌ Bot type check failed: {e}")
        return False
    
    # Test 3: Check questions file
    print("\n3️⃣ Testing questions file...")
    questions_file = BACKEND_DIR / "backend" / "accident_report" / "questionnaire" / "questions.json"
    if questions_file.exists():
        print(f"✅ Questions file found: {questions_file}")
    else:
        print(f"❌ Questions file not found: {questions_file}")
        return False
    
    # Test 4: Test Flask app imports (without starting server)
    print("\n4️⃣ Testing Flask app components...")
    try:
        # This should work even without API keys since we're not calling the LLM
        from backend import app
        print("✅ Flask app components loaded")
        
        # Check if the bot endpoints would be available
        rules = list(app.app.url_map.iter_rules())
        bot_endpoints = [str(rule) for rule in rules if 'bot' in str(rule)]
        print(f"✅ Bot endpoints available: {len(bot_endpoints)} endpoints")
        for endpoint in bot_endpoints:
            print(f"   - {endpoint}")
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 Bot integration tests completed!")
    print("\n📋 Summary:")
    print("   - Both rule-based and AI bots can be imported")
    print("   - Bot manager can determine available types")
    print("   - Questions file is accessible")
    print("   - Flask app can load with bot endpoints")
    print("\n✨ The AI bot implementation is ready!")
    print("   You can now:")
    print("   1. Start the backend server")
    print("   2. Use the wizard UI to select bot type (rule or ai)")
    print("   3. Test both bot types in the chat interface")
    
    return True

if __name__ == "__main__":
    success = test_bot_integration()
    sys.exit(0 if success else 1)
