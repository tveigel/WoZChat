# Accident Report Bot System

This directory contains the complete accident report bot system for WebWOz.

## 📁 Directory Structure

```
accident_report/
├── 📂 rule_based/           # Core bot logic
│   ├── bot_naive.py        # Main bot workflow and state management
│   └── validator.py        # Input validation and form processing
├── 📂 LLM/                 # LLM-based bot components
│   ├── bot_example.py      # Example LLM bot implementation
│   └── llm_config.py       # LLM configuration and setup
├── 📂 questionnaire/       # Form definitions and questions
│   └── questions.json      # Accident report form structure
├── 📂 tests/              # All test files
├── 📂 data/               # Sample data and visualizations
├── 📂 scripts/            # Analysis and debugging utilities
└── .env                   # Environment configuration
```

## 🤖 Bot Components

### Core System (`rule_based/`)
- **`bot_naive.py`**: Main bot workflow using LangGraph state machine
- **`validator.py`**: Form validation with comprehensive error handling

### LLM Integration (`LLM/`)
- **`bot_example.py`**: Example implementation using LLM providers
- **`llm_config.py`**: Configuration for various LLM services

### Configuration (`questionnaire/`)
- **`questions.json`**: Defines the accident report form structure and validation rules

## 🧪 Testing

All test files are located in the `tests/` directory. See [`tests/README.md`](./tests/README.md) for details.

## 📊 Data & Analysis

Sample data and analysis scripts are in their respective directories:
- [`data/README.md`](./data/README.md) - Sample forms and visualizations
- [`scripts/README.md`](./scripts/README.md) - Analysis and debugging tools

## 🚀 Usage

To use the accident report bot in your WebWOz application:

```python
from backend.accident_report.rule_based.bot_naive import FormWorkflow
from backend.accident_report.rule_based.validator import validate_answer

# Initialize the bot workflow
workflow = FormWorkflow()

# Process user input
result = validate_answer(user_input, question_config)
```

## 🔧 Development

For development and debugging:
1. Run tests: `python -m pytest tests/`
2. Analyze data: See scripts in `scripts/`
3. Validate forms: Use utilities in `data/`
