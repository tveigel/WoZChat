#!/usr/bin/env python3

"""
Quick test script to verify the improved bot works correctly
"""

import sys
import os

# Add the current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import required modules
    from bot_naive import FormWorkflow
    from validator import validate_answer
    import json
    
    print("✅ All imports successful!")
    
    # Test the validator with some basic inputs
    print("\n🧪 Testing validator...")
    
    # Test text validation
    text_question = {"type": "text", "id": "test"}
    is_valid, result = validate_answer(text_question, "SUV / Honda / CR-V")
    print(f"Text validation: {is_valid}, {result}")
    
    # Test number validation
    number_question = {"type": "number", "id": "test"}
    is_valid, result = validate_answer(number_question, "30")
    print(f"Number validation: {is_valid}, {result}")
    
    # Test choice validation
    choice_question = {
        "type": "single_choice", 
        "id": "test",
        "options": ["Straight", "Turning-Left", "Turning-Right"]
    }
    is_valid, result = validate_answer(choice_question, "Turning-Left")
    print(f"Choice validation: {is_valid}, {result}")
    
    print("\n🏗️ Testing FormWorkflow initialization...")
    
    # Test form workflow initialization (but don't run it interactively)
    questions_file = "../questionnaire/questions.json"
    if os.path.exists(questions_file):
        workflow = FormWorkflow(questions_file, interactive=False)
        print("✅ FormWorkflow initialized successfully!")
        
        # Test getting questions
        question = workflow.get_question_by_id("vehicles")
        if question:
            print(f"✅ Found vehicles question: {question['type']}")
            print(f"   Fields: {len(question.get('fields', []))}")
        else:
            print("❌ Could not find vehicles question")
    else:
        print(f"❌ Questions file not found at: {questions_file}")
    
    print("\n🎉 All tests completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required packages are installed:")
    print("  - langgraph")
    print("  - langchain_core")
    print("  - python-dateutil")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
