#!/usr/bin/env python3

import sys
import os
# Add the project root to Python path so imports work  
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from backend.accident_report.rule_based.bot_naive import FormWorkflow
import json

def test_bot_simple():
    """Test the bot with simulated inputs"""
    
    # Load questions to understand structure
    with open('../questionnaire/questions.json', 'r') as f:
        questions = json.load(f)
    
    print("Questions loaded:")
    for i, q in enumerate(questions["questions"][:5]):  # First 5 questions
        print(f"{i+1}. {q['id']}: {q['question'][:50]}...")
    
    print("\nBot seems to compile correctly!")

if __name__ == "__main__":
    test_bot_simple()
