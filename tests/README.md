# Tests

This folder contains all test files for the WebWOz project.

## Test Files

### 🔧 [test_integration.py](./test_integration.py)
Integration tests for the complete WebWOz system including:
- WebSocket communication
- Bot integration
- Template management
- Persistent storage

### 💾 [test_persistence.py](./test_persistence.py)
Specific tests for the persistent storage system:
- Database connectivity
- File-based fallback
- Data integrity
- Hybrid storage manager

## Running Tests

From the project root directory:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_integration.py
python tests/test_persistence.py

# Run with verbose output
python -m pytest tests/ -v
```

## Test Environment

Tests are designed to work with both:
- Development environment (file-based storage)
- Production environment (PostgreSQL database)

The hybrid storage system automatically handles fallback scenarios during testing.
