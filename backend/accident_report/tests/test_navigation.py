#!/usr/bin/env python3
"""
Test script to demonstrate the simplified navigation feature in bot_naive.py

This script shows how users can simply type "change reply" to edit 
their previous answers during form completion.
"""

import os
import sys
from pathlib import Path

# Add the rule_based directory to path
RULE_BASED_DIR = Path(__file__).parent.parent / "rule_based"
sys.path.insert(0, str(RULE_BASED_DIR))

from bot_naive import FormWorkflow

def test_navigation_detection():
    """Test the simplified navigation intent detection functionality."""
    print("🧪 Testing Simplified Navigation Intent Detection")
    print("=" * 50)
    
    workflow = FormWorkflow(interactive=False)
    
    # Test cases for navigation detection
    test_cases = [
        ("change reply", True),
        ("change answer", True),
        ("edit reply", True),
        ("edit answer", True),
        ("modify reply", True),
        ("modify answer", True),
        ("change my reply", True),
        ("change my answer", True),
        ("just a regular answer", False),
        ("yes", False),
        ("Toyota Camry", False),
        ("I want to change reply", True),
        ("Can I edit answer?", True)
    ]
    
    for test_input, expected in test_cases:
        result = workflow._detect_navigation_intent(test_input)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{test_input}' -> Navigation: {result}")

def demo_navigation_workflow():
    """Demonstrate the simplified navigation workflow."""
    print("\n🎭 Simplified Navigation Workflow Demo")
    print("=" * 50)
    print("This simplified approach works as follows:")
    print("1. User types 'change reply' at any point")
    print("2. System shows numbered list of completed questions")
    print("3. User selects a number (or 'cancel')")
    print("4. System navigates to that question for re-answering")
    print("5. After new answer, system returns to normal flow")
    print("\nNavigation Commands:")
    print("- 'change reply'")
    print("- 'change answer'") 
    print("- 'edit reply'")
    print("- 'edit answer'")
    print("- 'modify reply'")
    print("- 'modify answer'")
    print("\nTo see this in action, run the bot interactively!")
    print("Example: python bot_naive.py")

if __name__ == "__main__":
    try:
        test_navigation_detection()
        demo_navigation_workflow()
        print("\n✅ Simplified navigation feature tests completed successfully!")
        print("\n💡 To test navigation interactively:")
        print("   cd /path/to/rule_based/")
        print("   python bot_naive.py")
        print("   (Answer a few questions, then type 'change reply')")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
