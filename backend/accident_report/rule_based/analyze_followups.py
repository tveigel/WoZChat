#!/usr/bin/env python3
"""
Simple test to check the follow-up question structure.
"""

import json
from pathlib import Path

# Load the questions file directly
questions_file = Path("../questionnaire/questions.json")

with open(questions_file, 'r') as f:
    questions_data = json.load(f)

print("🔍 Analyzing Follow-up Questions Structure")
print("=" * 50)

# Find questions with follow-up logic
followup_questions = []
for q in questions_data["questions"]:
    if "followup_if_yes" in q:
        followup_questions.append(q)

print(f"Found {len(followup_questions)} questions with follow-ups:")

for i, q in enumerate(followup_questions):
    print(f"\n{i+1}. Main Question: {q['id']} - {q['question']}")
    print(f"   Type: {q['type']}")
    
    followup = q["followup_if_yes"]
    print(f"   Follow-up: {followup['id']} - {followup['question'][:100]}...")
    print(f"   Follow-up Type: {followup['type']}")
    
    if followup['type'] == 'table':
        print(f"   Table Columns: {len(followup['columns'])}")
        for col in followup['columns']:
            print(f"     - {col['id']}: {col['question'][:50]}...")

print(f"\n✅ Found {len(followup_questions)} questions with follow-up logic")
print("The bot needs to handle these follow-up questions properly.")

# Test the validator import
try:
    import sys
    sys.path.append('.')
    from validator import validate_answer
    
    # Test boolean validation
    bool_q = {"type": "boolean"}
    tests = ["yes", "1", "true", "no", "false", "maybe"]
    
    print(f"\n🧪 Testing Boolean Validation:")
    for test_val in tests:
        is_valid, result = validate_answer(bool_q, test_val)
        print(f"  '{test_val}' -> {is_valid}: {result}")
        
except ImportError as e:
    print(f"⚠️ Could not import validator: {e}")

print("\n🎯 Key Issues to Fix:")
print("1. Follow-up questions (especially 'table' type) need special handling")
print("2. Bot needs to ask follow-up questions after boolean 'yes' answers")
print("3. Table questions should be simplified to text for user-friendliness")
