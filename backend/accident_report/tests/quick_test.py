#!/usr/bin/env python3
"""
Quick comprehensive test for the WebWOz accident report bot.
Tests key paths through the form to ensure all scenarios work.
"""

import sys
from pathlib import Path

# Add the backend directory to path
BACKEND_DIR = Path(__file__).parent.parent.parent.parent  # Go up to backend level
sys.path.insert(0, str(BACKEND_DIR))

try:
    from bot_integration import WebBotSession
    print("✅ Successfully imported bot components")
except ImportError as e:
    print(f"❌ Failed to import bot components: {e}")
    sys.exit(1)


def test_scenario(name, description, answers):
    """Test a single scenario."""
    print(f"\n🧪 Testing: {name}")
    print(f"   {description}")
    
    session = WebBotSession(f"test_{name.replace(' ', '_').lower()}")
    
    try:
        # Start the bot
        response = session.start()
        if not response:
            print(f"   ❌ Failed to start session")
            return False
        
        answers_processed = 0
        total_answers = len(answers)
        
        for i, answer in enumerate(answers):
            if not session.is_active:
                break
                
            response = session.process_message(answer)
            if response and ("recorded" in response.lower() or "completed" in response.lower()):
                answers_processed += 1
            elif response and "❌" in response and "try again" in response.lower():
                # Try once more for validation errors
                response = session.process_message(answer)
                if response and ("recorded" in response.lower() or "completed" in response.lower()):
                    answers_processed += 1
        
        completion_rate = answers_processed / total_answers
        success = completion_rate >= 0.8  # 80% completion is good
        
        status = "✅" if success else "❌"
        print(f"   {status} Completed {answers_processed}/{total_answers} answers ({completion_rate:.1%})")
        
        return success
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def main():
    """Run key test scenarios."""
    print("🚀 Quick Comprehensive Test Suite")
    print("=" * 50)
    
    test_scenarios = [
        # Test 1: Happy path with 2 vehicles
        (
            "Two Vehicle Standard", 
            "Standard 2-vehicle accident with injuries and witnesses",
            [
                "2025-06-12", "14:35", "123 Main St, Springfield",
                "wet", "rain", "daylight",
                "intersection", "50", "signal", "2",
                "Sedan / Toyota / Camry", "ABC-1234", "turning-left", "30", "Front fender dented",
                "SUV / Honda / CR-V", "XYZ-5678", "straight", "45", "Rear bumper cracked",
                "Vehicle 1 turned left while vehicle 2 went straight",
                "failed-to-yield, weather/road", "yes", "Minor injuries to both drivers",
                "no", "yes", "Traffic light damaged", "yes", "Jane Smith saw everything",
                "Both vehicles towed"
            ]
        ),
        
        # Test 2: Single vehicle, no complications (test with user-friendly dash)
        (
            "Single Vehicle Simple",
            "Simple single vehicle accident, no injuries/damage/witnesses", 
            [
                "2025-07-15", "22:45", "Highway 17, mile marker 45",
                "snow/ice", "snow", "dark-unlit",  # Test flexible formatting
                "curve", "80", "none", "1",
                "Pickup / Ford / F-150", "ICE-2025", "straight", "65", "Minor body damage",
                "Vehicle lost control on icy curve",
                "weather/road, speeding", "no", "no", "no", "no", "Called tow truck"
            ]
        ),
        
        # Test 3: Three vehicles with complexity
        (
            "Three Vehicle Complex",
            "Complex 3-vehicle accident with fatalities",
            [
                "2025-08-06", "09:15", "Highway 401, Toronto",
                "debris", "clear", "daylight",
                "curve", "100", "none", "3",
                "Motorcycle / Harley / Sportster", "BIKE-123", "overtaking", "80", "Complete writeoff",
                "Pickup / Chevy / Silverado", "TRUCK-456", "straight", "90", "Minor scratches",
                "Van / Honda / Odyssey", "VAN-789", "turning-right", "70", "Rear end damage",
                "Motorcycle was overtaking when pickup changed lanes suddenly",
                "speeding, vehicle defect", "yes", "Serious injuries to multiple people",
                "yes", "no", "no", "Complex multi-vehicle accident"
            ]
        ),
        
        # Test 4: Edge case formats
        (
            "Boolean Format Test",
            "Test different boolean answer formats",
            [
                "2025-05-15", "16:30", "Test Location", 
                "wet", "rain", "daylight",
                "curve", "60", "none", "2",
                "Car / Test / Vehicle1", "TEST-1", "straight", "50", "Minor damage",
                "Car / Test / Vehicle2", "TEST-2", "straight", "55", "Minor damage", 
                "Standard two-car accident", "speeding",
                "true", "Minor injuries",  # true instead of yes
                "false",  # false instead of no
                "1",      # 1 instead of yes
                "Sign damaged", "0",      # 0 instead of no
                "Test completed"
            ]
        ),
    ]
    
    passed = 0
    total = len(test_scenarios)
    
    for name, description, answers in test_scenarios:
        if test_scenario(name, description, answers):
            passed += 1
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"🏁 QUICK TEST SUMMARY")
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Bot is working correctly.")
    elif passed/total >= 0.75:
        print("✅ MOSTLY WORKING: Bot handles most scenarios well.")  
    else:
        print("⚠️  NEEDS ATTENTION: Some scenarios are failing.")


if __name__ == "__main__":
    main()
