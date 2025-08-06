#!/usr/bin/env python3
import sys
sys.path.append('/home/qte9306/Documents/WebWoz_Home/WebWOz/backend/accident_report/rule_based')

from validator import _normalize_text

# Debug the normalization
q_def = {
    "type": "single_choice", 
    "options": ["1", "2", "3", "Other"],
    "other_specify": True
}

opts = {_normalize_text(o): o for o in q_def["options"]}
print("Normalized options dict:", opts)
print("Input '4' normalized:", _normalize_text("4"))
print("Is '4' in opts?", _normalize_text("4") in opts)

# Check each step
key = _normalize_text("4")
print(f"\nStep by step for input '4':")
print(f"1. key = '{key}'")
print(f"2. key.isdigit() = {key.isdigit()}")
if key.isdigit():
    idx = int(key) - 1
    print(f"3. idx = {idx}")
    print(f"4. 0 <= idx < len(options) = {0 <= idx < len(q_def['options'])}")
    if not (0 <= idx < len(q_def["options"])):
        print(f"5. other_specify = {q_def.get('other_specify')}")
        print(f"6. 'Other' in options = {'Other' in q_def['options']}")
