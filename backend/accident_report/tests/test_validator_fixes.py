#!/usr/bin/env python3
"""
Test the improved validator to ensure it handles character variations.
"""

import sys
from pathlib import Path

# Add the backend directory to path
BACKEND_DIR = Path(__file__).parent.parent.parent.parent  # Go up to backend level  
sys.path.insert(0, str(BACKEND_DIR))

try:
    from backend.accident_report.rule_based.validator import validate_answer
    print("✅ Successfully imported validator")
except ImportError as e:
    print(f"❌ Failed to import validator: {e}")
    sys.exit(1)

def test_validator_fixes():
    """Test that the validator now handles character variations correctly."""
    print("🧪 Testing Validator Character Normalization")
    print("=" * 50)
    
    test_cases = [
        # Test em dash vs hyphen
        {
            "name": "Em dash vs hyphen",
            "q_def": {"type": "single_choice", "options": ["Dark–Lit", "Dark–Unlit"]},
            "inputs": ["dark-lit", "dark-unlit", "Dark–Lit", "DARK-LIT"],
            "should_pass": True
        },
        
        # Test various dash types  
        {
            "name": "Various dash types",
            "q_def": {"type": "single_choice", "options": ["Snow / Ice"]},
            "inputs": ["snow / ice", "Snow / Ice", "snow/ice", "snow-ice"],
            "should_pass": True
        },
        
        # Test spacing variations
        {
            "name": "Spacing variations", 
            "q_def": {"type": "single_choice", "options": ["Dusk / Dawn", "Turning-Left"]},
            "inputs": ["dusk/dawn", "dusk / dawn", "turning left", "turning-left"],
            "should_pass": True
        },
        
        # Test case insensitivity
        {
            "name": "Case insensitivity",
            "q_def": {"type": "single_choice", "options": ["Intersection", "Straight"]},
            "inputs": ["INTERSECTION", "intersection", "straight", "STRAIGHT"],
            "should_pass": True
        },
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}:")
        print(f"   Options: {test_case['q_def']['options']}")
        
        for input_val in test_case['inputs']:
            total_tests += 1
            is_valid, result = validate_answer(test_case['q_def'], input_val)
            
            if is_valid == test_case['should_pass']:
                print(f"   ✅ '{input_val}' -> {result}")
                passed_tests += 1
            else:
                print(f"   ❌ '{input_val}' -> {'FAILED' if not is_valid else 'UNEXPECTED PASS'}: {result}")
    
    print(f"\n" + "=" * 50)
    print(f"🏁 VALIDATOR TEST SUMMARY")
    print(f"Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 ALL VALIDATOR TESTS PASSED!")
        return True
    else:
        print("⚠️  Some validator tests failed.")
        return False

if __name__ == "__main__":
    test_validator_fixes()
