#!/usr/bin/env python3
import sys
sys.path.append('/home/qte9306/Documents/WebWoz_Home/WebWOz/backend/accident_report/rule_based')

from validator import validate_answer

# Test the validator fixes
def test_validator_fixes():
    print("🧪 Testing Validator Fixes")
    print("=" * 40)
    
    # Test 1: Optional field with blank text
    print("\n📋 Test 1: Optional field with blank text")
    q_def = {
        "type": "text",
        "question": "Do you have any additional comments regarding the accident? (optional)"
    }
    is_valid, result = validate_answer(q_def, "")
    print(f"  Blank input for optional field: {'✅ PASS' if is_valid else '❌ FAIL'} - {result}")
    
    # Test 2: Required field with blank text (should fail)
    print("\n📋 Test 2: Required field with blank text")
    q_def = {
        "type": "text", 
        "question": "What is your name?"
    }
    is_valid, result = validate_answer(q_def, "")
    print(f"  Blank input for required field: {'✅ PASS' if not is_valid else '❌ FAIL'} - {result}")
    
    # Test 3: Number as other choice
    print("\n📋 Test 3: Number as other choice")
    q_def = {
        "type": "single_choice",
        "options": ["1", "2", "3", "Other"],
        "other_specify": True
    }
    is_valid, result = validate_answer(q_def, "4")
    expected_result = {"choice": "Other", "other": "4"}
    print(f"  Number '4' with other_specify: {'✅ PASS' if result == expected_result else '❌ FAIL'} - Got: {result}, Expected: {expected_result}")
    
    # Test 3b: Just "other" alone (should prompt for specification)
    is_valid, result = validate_answer(q_def, "other")
    print(f"  Just 'other' alone: {'✅ PASS' if not is_valid else '❌ FAIL'} - {result}")
    
    # Test 3c: "other 5" compound
    is_valid, result = validate_answer(q_def, "other 5")
    print(f"  'other 5' compound: {'✅ PASS' if is_valid else '❌ FAIL'} - {result}")
    
    # Test 3d: Free text for other_specify
    is_valid, result = validate_answer(q_def, "Heavy blizzard conditions")
    print(f"  Free text as other: {'✅ PASS' if is_valid else '❌ FAIL'} - {result}")
    
    # Test 3e: Normal index selection should still work
    is_valid, result = validate_answer(q_def, "2")
    print(f"  Normal index '2': {'✅ PASS' if result == '2' else '❌ FAIL'} - {result}")
    
    # Test 4: Character normalization
    print("\n📋 Test 4: Character normalization")
    q_def = {
        "type": "single_choice",
        "options": ["Daylight", "Dark–Lit", "Dark–Unlit"]
    }
    is_valid, result = validate_answer(q_def, "dark-lit")
    print(f"  'dark-lit' matching 'Dark–Lit': {'✅ PASS' if is_valid else '❌ FAIL'} - {result}")

if __name__ == "__main__":
    test_validator_fixes()
