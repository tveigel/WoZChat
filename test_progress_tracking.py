#!/usr/bin/env python3
"""
Test script to verify the improved progress tracking logic.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Test the bot integration progress tracking
from backend.bot_integration import WebBotSession

def test_progress_tracking():
    """Test the progress tracking functionality."""
    print("🧪 Testing Bot Progress Tracking")
    print("=" * 50)
    
    # Create a bot session
    room_id = "test_progress_room"
    bot_session = WebBotSession(room_id)
    
    if not bot_session.workflow:
        print("❌ Bot workflow not available - check configuration")
        return
    
    print(f"✅ Bot session created for room: {room_id}")
    print(f"📊 Total questions in workflow: {len(bot_session.workflow.questions)}")
    
    # Start the bot
    print("\n" + "─" * 30)
    print("📋 STARTING BOT SESSION")
    print("─" * 30)
    
    initial_message = bot_session.start()
    if initial_message:
        print("🤖 Initial bot message:")
        print(initial_message)
        print()
    
    # Get initial status
    status = bot_session.get_status()
    print(f"📈 Initial Status: {status}")
    
    # Test progress calculation with different states
    print("\n" + "─" * 30)
    print("🔍 TESTING PROGRESS SCENARIOS")
    print("─" * 30)
    
    # Simulate different question states
    test_states = [
        {
            "description": "Simple question",
            "state": {
                "questions_completed": [],
                "current_question_index": 0,
                "current_question_id": "q1"
            }
        },
        {
            "description": "After completing first question",
            "state": {
                "questions_completed": ["q1"],
                "current_question_index": 1,
                "current_question_id": "q2"
            }
        },
        {
            "description": "Retry scenario (same question)",
            "state": {
                "questions_completed": ["q1"],
                "current_question_index": 1,
                "current_question_id": "q1",  # Same as completed
                "last_error": "Invalid format. Please try again."
            }
        },
        {
            "description": "Group question",
            "state": {
                "questions_completed": ["q1"],
                "current_question_index": 1,
                "current_question_id": "q2",
                "current_group_question": {"fields": ["field1", "field2", "field3"]},
                "current_group_field_index": 1
            }
        },
        {
            "description": "Repeat group (vehicle details)",
            "state": {
                "questions_completed": ["q1", "q2"],
                "current_question_index": 2,
                "current_question_id": "q3",
                "current_repeat_group_question": {"fields": ["make", "model", "damage"]},
                "current_repeat_instance": 1,  # Second vehicle
                "current_repeat_field_index": 0  # First field of second vehicle
            }
        }
    ]
    
    for i, test_case in enumerate(test_states):
        print(f"\n{i+1}. {test_case['description']}:")
        
        # Temporarily set the state
        original_state = bot_session.current_state
        bot_session.current_state = test_case['state']
        
        # Calculate progress
        progress = bot_session._calculate_progress()
        print(f"   Progress: {progress}")
        
        # Restore original state
        bot_session.current_state = original_state
    
    print("\n" + "=" * 50)
    print("✅ Progress tracking test completed!")

if __name__ == "__main__":
    test_progress_tracking()
