from __future__ import annotations
from typing import Any, Dict, List, Tuple
from dateutil import parser as dt_parser
import re
import json

def validate_answer(q_def: Dict[str, Any], reply: str) -> Tuple[bool, Any]:
    """
    Validate a single user reply against one question definition.
    Returns (is_valid, converted_value).  If is_valid == False, the second
    element holds an error string explaining the problem.
    """
    q_type = q_def["type"]

    try:
        if q_type == "date":
            value = _parse_date(reply)
        elif q_type == "time":
            value = _parse_time(reply)
        elif q_type in {"text", "multiline_text"}:
            value = reply.strip()
            # Allow blank text for optional fields (those with "(optional)" in question text)
            if not value and not q_def.get("question", "").lower().endswith("(optional)"):
                raise ValueError("blank text")
        elif q_type == "number":
            value = _parse_number(reply)
        elif q_type == "boolean":
            value = _parse_bool(reply)
        elif q_type in {"single_choice", "multiple_choice"}:
            value = _parse_choice(reply, q_def, multi=(q_type == "multiple_choice"))
        elif q_type == "group":
            value = _parse_group(reply, q_def)
        elif q_type == "repeat_group":
            value = _parse_repeat_group(reply, q_def)
        elif q_type == "table":
            value = _parse_table(reply, q_def)
        else:
            return False, f"Unknown q_type \"{q_type}\""
    except ValueError as err:
        return False, str(err)

    return True, value

def _parse_date(s: str):
    return dt_parser.parse(s).date()

def _parse_time(s: str):
    s = s.strip()
    
    # Check if it's just a number (like "2") - this is ambiguous
    if s.isdigit() and len(s) <= 2:
        raise ValueError("Time format unclear. Please use HH:MM format (e.g., 14:35 or 02:00)")
    
    # Try to parse the time
    try:
        parsed_time = dt_parser.parse(s).time()
        # Additional validation - if seconds weren't specified, make sure it's reasonable
        if parsed_time.hour == 0 and parsed_time.minute == 0 and parsed_time.second == 0 and s != "00:00" and s != "0:00":
            raise ValueError("Time format unclear. Please use HH:MM format (e.g., 14:35 or 02:00)")
        return parsed_time
    except Exception:
        raise ValueError("Invalid time format. Please use HH:MM format (e.g., 14:35 or 02:00)")

def _parse_number(s: str):
    # Extract numeric part from strings like "30 kmh", "thirty", etc.
    s = s.strip().lower()
    
    # Handle written numbers
    word_to_num = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
        'eighty': 80, 'ninety': 90, 'hundred': 100
    }
    
    if s in word_to_num:
        return word_to_num[s]
    
    # Extract numbers from strings with units (e.g., "30 kmh", "50 km/h")
    import re
    num_match = re.search(r'-?\d+(?:\.\d+)?', s)
    if num_match:
        num_str = num_match.group()
        return int(num_str) if re.fullmatch(r"-?\d+", num_str) else float(num_str)
    
    # Fallback to original parsing
    return int(s) if re.fullmatch(r"-?\d+", s.strip()) else float(s)

_BOOL_TRUE = {"yes", "y", "true", "t", "1"}
_BOOL_FALSE = {"no", "n", "false", "f", "0"}
def _parse_bool(s: str):
    lowered = s.strip().lower()
    if lowered in _BOOL_TRUE:
        return True
    if lowered in _BOOL_FALSE:
        return False
    raise ValueError("expected yes/no or true/false")

def _normalize_text(text: str) -> str:
    """Normalize text for comparison by handling common character variations."""
    text = text.lower().strip()
    # Replace various dash types with regular hyphen
    text = text.replace('–', '-').replace('—', '-').replace('−', '-')  # em dash, en dash, minus
    # Replace various quote types
    text = text.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
    # Normalize spacing around slashes and hyphens
    text = re.sub(r'\s*/\s*', '/', text)  # "snow / ice" -> "snow/ice"
    text = re.sub(r'\s*-\s*', '-', text)  # "dark - lit" -> "dark-lit"
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def _parse_choice(s: str, q_def: Dict[str, Any], *, multi: bool):
    raw = [p.strip() for p in re.split(r",|;", s) if p.strip()] if multi else [s.strip()]
    opts = {_normalize_text(o): o for o in q_def["options"]}
    canonical: List[str] = []

    for part in raw:
        key = _normalize_text(part.rstrip('.'))
        
        # Check if it's a compound "other" response like "other 4" or "4 vehicles"
        if q_def.get("other_specify"):
            # Handle various "other" patterns
            other_patterns = [
                r'^other\s+(.+)',  # "other 4"
                r'^(.+)\s+other$',  # "4 other" 
                r'^other:\s*(.+)',  # "other: 4"
                r'^other\s*-\s*(.+)',  # "other - 4"
            ]
            
            for pattern in other_patterns:
                other_match = re.search(pattern, key, re.IGNORECASE)
                if other_match:
                    specification = other_match.group(1).strip()
                    if specification:
                        return {"choice": "Other", "other": specification}
            
            # If just "other" alone - ask for specification  
            if key.lower() in ["other", "else", "different", "something else", "misc", "miscellaneous"]:
                raise ValueError("Please specify what 'other' option you mean (e.g., '4 vehicles' or 'other: heavy blizzard')")
            
            # If it's not a match for existing options but other_specify is true, 
            # treat any unmatched input as an "other" specification
            unmatched_as_other = True
        else:
            unmatched_as_other = False
        
        # Check direct text match first (most explicit)
        if key in opts:
            canonical.append(opts[key])
        else:
            found_match = False
            
            # Check if it's a number that could be either an index or a value
            if key.isdigit():
                idx = int(key) - 1
                # If it's a valid 1-based index for the options
                if 0 <= idx < len(q_def["options"]):
                    # But if it's a numeric value question with other_specify, 
                    # prefer treating it as a value rather than index
                    # (e.g., "4" for vehicle count should mean "4 vehicles", not "4th option")
                    if (q_def.get("other_specify") and 
                        all(opt.isdigit() or opt == "Other" for opt in q_def["options"]) and
                        int(key) not in [int(opt) for opt in q_def["options"] if opt.isdigit()]):
                        # This number is not in the explicit options, treat as "other" value
                        return {"choice": "Other", "other": part}
                    else:
                        # Normal index selection
                        canonical.append(q_def["options"][idx])
                        found_match = True
                # If it's a number but not a valid index, and other_specify is True
                elif q_def.get("other_specify"):
                    return {"choice": "Other", "other": part}
            
            if not found_match:
                # Check if the user input contains any of the option words (fuzzy matching)
                for option_key, option_value in opts.items():
                    # Handle special case where option is "None" and user types "none"
                    if _normalize_text(option_value) == "none" and key == "none":
                        canonical.append(option_value)
                        found_match = True
                        break
                    # Check if either string contains the other (partial matching)
                    elif option_key in key or key in option_key:
                        canonical.append(option_value)
                        found_match = True
                        break
                    # Check for word-based matching with flexible separators
                    elif _flexible_word_match(key, option_key):
                        canonical.append(option_value)
                        found_match = True
                        break
            
            if not found_match:
                if unmatched_as_other:
                    # Treat unmatched input as "other" specification
                    if multi:
                        canonical.append(part)
                        return {"choices": canonical, "other": part}
                    else:
                        return {"choice": "Other", "other": part}
                else:
                    raise ValueError(f"\"{part}\" not a valid option")

    if multi:
        return canonical
    else:
        return canonical[0] if canonical else None

def _flexible_word_match(input_text: str, option_text: str) -> bool:
    """Check if two texts match when considering flexible word separators."""
    # Split by common separators and compare word sets
    input_words = re.split(r'[-/\s]+', input_text.lower())
    option_words = re.split(r'[-/\s]+', option_text.lower())
    
    # Remove empty strings
    input_words = [w for w in input_words if w]
    option_words = [w for w in option_words if w]
    
    # Check if word sets are equal
    return set(input_words) == set(option_words)

def _parse_group(reply: str, q_def: Dict[str, Any]):
    try:
        obj = json.loads(reply)
    except json.JSONDecodeError:
        raise ValueError("group reply must be JSON")

    parsed = {}
    for fld in q_def["fields"]:
        ok, val = validate_answer(fld, obj.get(fld["id"], ""))
        if not ok:
            raise ValueError(f"{fld['id']}: {val}")
        parsed[fld["id"]] = val
    return parsed

def _parse_repeat_group(reply: str, q_def: Dict[str, Any]):
    try:
        arr = json.loads(reply)
        assert isinstance(arr, list)
    except Exception:
        raise ValueError("repeat_group reply must be JSON list")

    return [_parse_group(json.dumps(elem), {"type": "group", "fields": q_def["fields"]})
            for elem in arr]

def _parse_table(reply: str, q_def: Dict[str, Any]):
    return _parse_repeat_group(reply, {"type": "repeat_group", "fields": q_def["columns"]})

def type_check(desired_type, value, node_name=None):
    ok, _ = validate_answer(desired_type, value)
    return "next_node" if ok else node_name
