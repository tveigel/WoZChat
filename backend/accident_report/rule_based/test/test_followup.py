#!/usr/bin/env python3
"""
Focused test for follow-up questions in the accident report bot.
"""

import sys
import json
from pathlib import Path

# Add the backend directory to path  
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

try:
    from bot_integration import WebBotSession
    print("✅ Successfully imported WebBotSession")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

def test_followup_questions():
    """Test follow-up question handling specifically."""
    print("🧪 Testing Follow-up Questions")
    print("=" * 40)
    
    session = WebBotSession("followup_test")
    
    # Start the bot
    response = session.start()
    print(f"📋 Start: {response[:100]}..." if response else "❌ No start response")
    
    # Quick answers to get to the injury question (question 12)
    quick_answers = [
        "2025-06-12",     # date
        "14:35",          # time  
        "123 Main St",    # location
        "dry",            # road surface
        "clear",          # weather
        "daylight",       # lighting
        "straight",       # location type (group 1)
        "50",             # speed limit (group 2)
        "none",           # traffic control (group 3)
        "1",              # number of vehicles
        "Car",            # vehicle type
        "ABC123",         # vehicle plate
        "straight",       # vehicle manoeuvre
        "50",             # vehicle speed
        "None",           # vehicle damage
        "Single vehicle accident",  # narrative
        "speeding",       # contributing factors
    ]
    
    print(f"\n🚀 Answering {len(quick_answers)} questions to reach injury question...")
    
    for i, answer in enumerate(quick_answers):
        response = session.process_message(answer)
        if response is None or "❌" in response:
            print(f"❌ Failed at question {i+1}: {response}")
            return False
        if i % 3 == 0:  # Progress update every 3 questions
            print(f"  ✅ Progress: {i+1}/{len(quick_answers)}")
    
    print(f"\n📋 Should now be at injury question. Current response:")
    print(f"Response: {response[:200]}..." if response else "No response")
    
    # Now test the injury follow-up
    print(f"\n🎯 Testing injury follow-up...")
    
    # Answer "yes" to injuries to trigger follow-up
    injury_response = session.process_message("yes")
    print(f"📋 Injury 'yes' response:")
    print(f"Response: {injury_response[:300]}..." if injury_response else "No response")
    
    if injury_response and "injury" in injury_response.lower():
        print("✅ Follow-up question triggered!")
        
        # Try to answer the follow-up
        followup_answer = "Driver had minor cuts, passenger had bruises"
        followup_response = session.process_message(followup_answer)
        print(f"📋 Follow-up answer response:")
        print(f"Response: {followup_response[:300]}..." if followup_response else "No response")
        
        if followup_response and "❌" not in followup_response:
            print("✅ Follow-up question answered successfully!")
            return True
        else:
            print("❌ Follow-up question failed!")
            return False
    else:
        print("❌ Follow-up question not triggered!")
        return False

def test_simple_followup():
    """Test a simpler follow-up scenario."""
    print("\n🧪 Testing Simple Follow-up")
    print("=" * 40)
    
    # Test the validator directly first
    from accident_report.rule_based.validator import validate_answer
    
    # Test boolean validation
    bool_question = {"type": "boolean"}
    is_valid, result = validate_answer(bool_question, "yes")
    print(f"Boolean validation: 'yes' -> {is_valid}, {result}")
    
    # Test follow-up logic in the FormWorkflow
    from accident_report.rule_based.bot_naive import FormWorkflow
    
    workflow = FormWorkflow("../questionnaire/questions.json", interactive=False)
    
    # Find the injury question
    injury_question = None
    for q in workflow.questions:
        if q["id"] == "any_injuries":
            injury_question = q
            break
    
    if injury_question:
        print(f"✅ Found injury question: {injury_question['question']}")
        if "followup_if_yes" in injury_question:
            followup = injury_question["followup_if_yes"]
            print(f"✅ Has follow-up: {followup['id']} - {followup['question'][:100]}...")
            print(f"Follow-up type: {followup['type']}")
        else:
            print("❌ No follow-up found!")
    else:
        print("❌ Injury question not found!")

if __name__ == "__main__":
    print("🚀 Starting Follow-up Question Tests")
    print("=" * 50)
    
    test_simple_followup()
    
    try:
        success = test_followup_questions()
        if success:
            print("\n🎉 Follow-up questions are working!")
        else:
            print("\n❌ Follow-up questions need fixing!")
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
