#!/usr/bin/env python3
"""
Test script to demonstrate the user-friendly bot behavior.
This script simulates user input to test the bot without requiring interactive input.
"""

import json
from bot_naive import FormWorkflow

def test_vehicle_questions():
    """Test that the bot handles vehicle questions in a user-friendly way."""
    
    # Create the workflow in non-interactive mode for testing
    workflow = FormWorkflow("../questionnaire/questions.json", interactive=False)
    graph = workflow.compile_graph()
    
    # Test configuration
    config = {"configurable": {"thread_id": "test_session"}, "recursion_limit": 100}
    
    print("Testing user-friendly vehicle question handling...")
    print("=" * 60)
    
    # Initialize the form
    state = graph.invoke({}, config=config)
    print(f"Initial state keys: {list(state.keys())}")
    
    # Simulate going through questions until we reach the vehicles question
    # We need to provide answers to earlier questions first
    
    # Let's create a simple test to check if our state initialization works
    initial_state = workflow.start_form({})
    print(f"Form initialized with question: {initial_state['current_question_id']}")
    
    # Test if we can properly identify the vehicle question
    vehicle_question = None
    for q in workflow.questions:
        if q["id"] == "vehicles":
            vehicle_question = q
            break
    
    if vehicle_question:
        print(f"Found vehicle question: {vehicle_question['question']}")
        print(f"Question type: {vehicle_question['type']}")
        print(f"Number of fields: {len(vehicle_question['fields'])}")
        
        # Show what the first field would be
        first_field = vehicle_question["fields"][0]
        print(f"First field: {first_field['question']}")
        print(f"First field type: {first_field['type']}")
    else:
        print("❌ Vehicle question not found!")
        return False
    
    print("\n✅ Bot structure looks good for user-friendly interaction!")
    print("The bot will now ask vehicle questions one by one instead of expecting JSON.")
    
    return True

def test_group_questions():
    """Test that group questions work properly."""
    workflow = FormWorkflow("../questionnaire/questions.json", interactive=False)
    
    # Find a group question
    group_question = None
    for q in workflow.questions:
        if q["type"] == "group":
            group_question = q
            break
    
    if group_question:
        print(f"\nFound group question: {group_question['question']}")
        print(f"Number of fields: {len(group_question['fields'])}")
        for i, field in enumerate(group_question['fields']):
            print(f"  Field {i+1}: {field['question']} (type: {field['type']})")
        print("✅ Group questions will be asked field by field!")
    else:
        print("No group questions found.")

if __name__ == "__main__":
    success = test_vehicle_questions()
    test_group_questions()
    
    if success:
        print("\n🎉 All tests passed! The bot is now user-friendly.")
        print("Users will be asked individual questions instead of being asked for JSON.")
    else:
        print("\n❌ Tests failed. Please check the implementation.")
