#!/usr/bin/env python3
"""
Test runner for accident_report tests.
Handles import paths properly.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def run_tests():
    """Run all tests in the tests directory"""
    tests_dir = Path(__file__).parent
    test_files = list(tests_dir.glob("test_*.py"))
    
    print(f"🧪 Found {len(test_files)} test files")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        print(f"\n▶️  Running {test_file.name}...")
        try:
            # Import and run the test
            spec = importlib.util.spec_from_file_location("test_module", test_file)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            # Look for test functions and run them
            for attr_name in dir(test_module):
                if attr_name.startswith('test_'):
                    test_func = getattr(test_module, attr_name)
                    try:
                        test_func()
                        print(f"  ✅ {attr_name}")
                        passed += 1
                    except Exception as e:
                        print(f"  ❌ {attr_name}: {e}")
                        failed += 1
                        
        except Exception as e:
            print(f"  ❌ Failed to run {test_file.name}: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    import importlib.util
    success = run_tests()
    sys.exit(0 if success else 1)
