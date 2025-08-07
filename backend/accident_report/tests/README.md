# Tests

This directory contains all test files for the accident report bot system.

## 🧪 Test Files

### Core System Tests
- **`test_validator.py`** - Validator function tests
- **`test_validator_fixes.py`** - Validator import and functionality tests
- **`test_improved_bot.py`** - Enhanced bot functionality tests
- **`test_integration.py`** - Integration tests for the complete system

### Workflow Tests
- **`test_bot.py`** - Basic bot workflow tests
- **`test_followup.py`** - Followup question handling tests
- **`test_user_friendly.py`** - User experience and interface tests

### Comprehensive Tests
- **`comprehensive_test.py`** - Full system validation and testing
- **`quick_test.py`** - Quick validation and smoke tests

## 🏃 Running Tests

### From Project Root (Recommended)
```bash
# Individual test files - run from project root
cd /path/to/WebWOz
python backend/accident_report/tests/test_validator.py
python backend/accident_report/tests/comprehensive_test.py

# Quick smoke test
python backend/accident_report/tests/quick_test.py

# Using pytest (if available)
python -m pytest backend/accident_report/tests/ -v
```

### Alternative Methods
```bash
# From accident_report directory
cd backend/accident_report
python tests/test_validator.py

# Using the test runner (handles imports automatically)
python tests/run_tests.py
```

## 🔧 Test Environment

Tests are designed to work with:
- Local development environment
- CI/CD pipelines
- Production validation

## 📝 Test Coverage

The tests cover:
- ✅ Form validation logic
- ✅ Bot workflow state management
- ✅ Error handling and edge cases
- ✅ Integration with WebWOz backend
- ✅ User input processing
- ✅ Followup question generation

## 🐛 Debugging

For debugging test failures:
1. Run individual tests with verbose output
2. Check test logs and error messages
3. Use debugging utilities in `../scripts/`
