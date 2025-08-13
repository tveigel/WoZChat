#!/usr/bin/env python3
"""
Test script for navigation edit functionality
Tests the intelligent navigation when users edit previous answers
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from navigation_analyzer import NavigationImpactAnalyzer
import json

def test_navigation_scenarios():
    """Test various navigation edit scenarios"""
    
    # Load questions for testing
    with open('../questionnaire/questions.json', 'r') as f:
        questions = json.load(f)
    
    analyzer = NavigationImpactAnalyzer(questions)
    
    print("🧪 Testing Navigation Edit Scenarios\n")
    
    # Test 1: Simple question edit (should continue)
    print("Test 1: Edit simple question (date of accident)")
    current_state = {
        'current_question_index': 15,
        'answers': {'date_of_accident': '2024-01-15'},
        'conversation_history': []
    }
    edited_question_id = 'date_of_accident'
    new_value = '2024-01-16'
    
    result = analyzer.analyze_edit_impact(edited_question_id, new_value, current_state)
    print(f"  📝 Edited: {edited_question_id}")
    print(f"  🎯 Current position: {current_state['current_question_index']}")
    print(f"  🧭 Navigation strategy: {result['strategy']}")
    print(f"  📍 Restart from: {result.get('restart_from_question_id', 'N/A')}")
    print(f"  💡 Reason: {result['reason']}\n")
    
    # Test 2: Branching question edit (should jump back)
    print("Test 2: Edit branching question (any injuries)")
    current_state = {
        'current_question_index': 20,
        'answers': {'any_injuries': True},
        'conversation_history': []
    }
    edited_question_id = 'any_injuries'
    new_value = False
    
    result = analyzer.analyze_edit_impact(edited_question_id, new_value, current_state)
    print(f"  📝 Edited: {edited_question_id}")
    print(f"  🎯 Current position: {current_state['current_question_index']}")
    print(f"  🧭 Navigation strategy: {result['strategy']}")
    print(f"  📍 Restart from: {result.get('restart_from_question_id', 'N/A')}")
    print(f"  💡 Reason: {result['reason']}\n")
    
    # Test 3: Repeat group trigger question edit
    print("Test 3: Edit repeat group trigger (number of vehicles)")
    current_state = {
        'current_question_index': 25,
        'answers': {'number_of_vehicles_involved': '2'},
        'conversation_history': []
    }
    edited_question_id = 'number_of_vehicles_involved'
    new_value = '3'
    
    result = analyzer.analyze_edit_impact(edited_question_id, new_value, current_state)
    print(f"  📝 Edited: {edited_question_id}")
    print(f"  🎯 Current position: {current_state['current_question_index']}")
    print(f"  🧭 Navigation strategy: {result['strategy']}")
    print(f"  📍 Restart from: {result.get('restart_from_question_id', 'N/A')}")
    print(f"  💡 Reason: {result['reason']}\n")
    
    # Test 4: Test dependency mapping
    print("Test 4: Dependency mapping")
    dependencies = analyzer.question_dependencies
    
    # Show some examples
    print(f"  🔗 Branching questions: {list(analyzer.branching_questions)[:3]}")
    print(f"  🔗 Repeat group triggers: {list(analyzer.repeat_group_triggers)[:3]}")
    
    for q_id, deps in list(dependencies.items())[:3]:
        if deps:
            print(f"  🔗 {q_id} → {deps}")
    
    print(f"\n✅ Tests completed! Found {len(analyzer.branching_questions)} branching questions and {len(analyzer.repeat_group_triggers)} repeat triggers.")

if __name__ == "__main__":
    test_navigation_scenarios()
