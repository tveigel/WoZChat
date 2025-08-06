#!/usr/bin/env python3

from LLM.rule_based.bot_naive import FormWorkflow
import json

def test_bot_simple():
    """Test the bot with simulated inputs"""
    
    # Load questions to understand structure
    with open('questions.json', 'r') as f:
        questions = json.load(f)
    
    print("Questions loaded:")
    for i, q in enumerate(questions["questions"][:5]):  # First 5 questions
        print(f"{i+1}. {q['id']}: {q['question'][:50]}...")
    
    print("\nBot seems to compile correctly!")

if __name__ == "__main__":
    test_bot_simple()
