#!/usr/bin/env python3

from LLM.rule_based.validator import validate_answer

def test_time_validation():
    print("Testing time validation:")
    time_q = {'type': 'time'}
    
    test_cases = ['2', '14:35', '2:30', '00:00']
    for case in test_cases:
        try:
            result = validate_answer(time_q, case)
            print(f'  "{case}" -> {result[1]} (valid: {result[0]})')
        except Exception as e:
            print(f'  "{case}" -> ERROR: {e}')

def test_choice_validation():
    print("\nTesting choice validation with None option:")
    choice_q = {'type': 'single_choice', 'options': ['Stop Sign', 'Signal', 'None']}
    
    test_cases = ['none', '3', 'None', 'signal']
    for case in test_cases:
        try:
            result = validate_answer(choice_q, case)
            print(f'  "{case}" -> {result[1]} (valid: {result[0]})')
        except Exception as e:
            print(f'  "{case}" -> ERROR: {e}')

def test_number_validation():
    print("\nTesting number validation:")
    num_q = {'type': 'number'}
    
    test_cases = ['30kmh', 'thirty', '50', '25.5 km/h']
    for case in test_cases:
        try:
            result = validate_answer(num_q, case)
            print(f'  "{case}" -> {result[1]} (valid: {result[0]})')
        except Exception as e:
            print(f'  "{case}" -> ERROR: {e}')

if __name__ == "__main__":
    test_time_validation()
    test_choice_validation()
    test_number_validation()
