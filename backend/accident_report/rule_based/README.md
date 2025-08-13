# Naive Rule-Based Bot Documentation

## Overview

The naive rule-based bot is a form-filling assistant that guides users through completing an accident report form using a deterministic, rule-based approach. It leverages LangGraph for workflow management and implements comprehensive validation logic to ensure data quality.

## Architecture

### Core Components

1. **`bot_naive.py`** - Main workflow implementation using LangGraph
2. **`validator.py`** - Input validation and parsing logic
3. **`ui_components.py`** - UI component generation for web interface
4. **`questions.json`** - Form question definitions and structure

### Key Features

- **Sequential Form Processing**: Guides users through questions in a predefined order
- **Multi-type Question Support**: Handles text, numbers, dates, choices, groups, and repeat groups
- **Clickable UI Components**: Web interface with clickable buttons for choice questions
- **Robust Validation**: Comprehensive input validation with error handling and retry logic
- **Conditional Logic**: Supports follow-up questions based on previous answers
- **Flexible Input Parsing**: Accepts various input formats (e.g., "30 km/h", "thirty", "3")
- **Interactive Navigation**: Users can navigate back to previous questions to modify answers
- **Interactive & Web Modes**: Can run interactively in terminal or as a web service
- **Dual Input Methods**: Users can click buttons OR type answers (backward compatible)

## Clickable UI Features

### Supported UI Components

- **Clickable Choice Questions**: Single and multiple choice questions display as clickable buttons (current question only)
- **"Other" Option Support**: When "other_specify" is enabled, users can select "Other" and provide custom text
- **Visual Feedback**: Selected options are highlighted with checkboxes for multiple choice
- **Auto-submission**: Single choice selections submit automatically (except when "Other" needs specification)
- **Fallback Support**: Always maintains text input compatibility for accessibility
- **Previous Question Display**: Previous questions are shown for reference but are not clickable

### UI Component Types

1. **ClickableChoiceComponent**: For single_choice and multiple_choice questions
   - Renders options as clickable buttons (for current question only)
   - Supports "other" specification with text input
   - Visual selection indicators (checkboxes for multiple choice)
   - Auto-submit for single selections
   - Previous questions shown for reference but disabled

2. **TextInputComponent**: For all other question types
   - Standard text inputs with appropriate types (text, number, date, time)
   - Context-specific placeholders and hints
   - Maintains full keyboard accessibility

### Navigation Edit System

The bot includes a classic navigation system that allows users to edit previous answers using explicit commands:

#### How Navigation Works

1. **Navigation Commands**: Users type explicit commands like "change reply" during the conversation
2. **Question Selection**: System shows a numbered list of completed questions
3. **Manual Selection**: Users select the question number they want to edit
4. **Smart Navigation**: The system uses intelligent logic to determine how to handle the edit:

#### Navigation Logic

- **Simple Questions**: For basic info (name, date, etc.), the bot updates the answer and continues from where it left off
- **Branching Questions**: For questions that affect the conversation flow (Yes/No follow-ups, conditional questions), the bot jumps back to the edited point and continues from there
- **Repeat Group Questions**: For questions that determine group counts, edits may add/remove entire question sets

#### Implementation Components

- **`navigation_analyzer.py`**: Analyzes edit impact and determines navigation strategy
- **`bot_naive.py`**: Enhanced with classic "change reply" navigation system
- **Frontend**: Displays previous questions for reference but they are not clickable

## Question Types Supported

### Basic Types
- **text/multiline_text**: Free-form text input
- **number**: Numeric values with flexible parsing
- **date**: Date inputs with natural language parsing
- **time**: Time inputs with format validation
- **boolean**: Yes/No questions with multiple accepted formats

### Choice Types
- **single_choice**: Select one option from a list
- **multiple_choice**: Select multiple options from a list
- **other_specify**: Choice questions with custom "other" option

### Complex Types
- **group**: Related fields grouped together (e.g., road conditions)
- **repeat_group**: Repeating sets of fields (e.g., vehicle details)
- **table**: Tabular data entry (e.g., injury reports)

### Conditional Logic
- **followup_if_yes**: Questions that appear based on boolean answers
- **Dynamic repeat counts**: Repeat groups that adapt to previous answers

### Navigation Features
- **Simple Reply Editing**: Users can type "change reply" to edit previous answers
- **Interactive Selection**: Shows numbered list of completed questions for easy selection
- **Quick Navigation**: Direct jump to any previously answered question

## File Structure

```
rule_based/
├── README.md              # This documentation
├── bot_naive.py           # Main workflow implementation
├── validator.py           # Input validation logic
├── __init__.py           # Package initialization
└── form_workflow_graph.png # Generated workflow visualization
```

## Core Classes and Methods

### FormState (TypedDict)

Maintains the complete state of the form-filling session:

```python
class FormState(TypedDict):
    messages: List[Message]                    # Conversation history
    current_question_id: str                   # ID of current question
    current_question_index: int               # Index in main question list
    form_data: Dict[str, Any]                 # Collected form responses
    questions_completed: List[str]            # List of completed question IDs
    retry_count: int                          # Current retry attempt
    last_error: Optional[str]                 # Last validation error
    form_complete: bool                       # Form completion status
    validation_success: bool                  # Last validation result
    
    # Group question handling
    current_group_question: Optional[Dict]    # Current group being processed
    current_group_field_index: int           # Field index within group
    group_data: Dict[str, Any]               # Data for current group
    
    # Repeat group handling
    current_repeat_group_question: Optional[Dict]  # Current repeat group
    current_repeat_instance: int                   # Instance number (0, 1, 2...)
    current_repeat_field_index: int               # Field index within instance
    repeat_group_data: List[Dict[str, Any]]       # Completed instances
    current_instance_data: Dict[str, Any]         # Data for current instance
    
    # Navigation functionality
    navigation_request: bool                       # Whether user wants to navigate back
    target_question_id: Optional[str]             # ID of question to navigate to
    question_history: List[Dict[str, Any]]        # History of completed questions
```

### FormWorkflow Class

The main class that orchestrates the form-filling process using LangGraph.

#### Key Methods

**Initialization and Setup**
- `__init__(questions_file, interactive=True)`: Initialize with question definitions
- `_build_graph()`: Construct the LangGraph workflow
- `compile_graph()`: Compile and return the executable graph

**Question Navigation**
- `get_question_by_id(question_id)`: Retrieve question definition by ID
- `get_next_question(current_index)`: Get next question in sequence
- `get_followup_question_by_id(question_id)`: Find follow-up questions

**Core Workflow Nodes**
- `start_form(state)`: Initialize form session
- `ask_question(state)`: Display current question
- `get_user_input(state)`: Collect user response (interactive mode)
- `check_navigation(state)`: Check if user wants to navigate to previous question
- `handle_navigation(state)`: Process navigation requests and update state
- `validate_input(state)`: Validate and parse user input
- `advance_to_next(state)`: Move to next question
- `handle_followup(state)`: Process conditional follow-up questions
- `handle_group_question(state)`: Manage group question progression
- `handle_repeat_group(state)`: Handle repeat group instances
- `complete_form(state)`: Finalize and save form data

**Routing Logic**
- `route_after_validation(state)`: Determine next step after validation
- `route_after_followup(state)`: Route after follow-up handling
- `route_after_group(state)`: Route after group completion
- `route_after_repeat_group(state)`: Route after repeat group handling
- `route_after_navigation_check(state)`: Route after checking for navigation intent

**Navigation Methods**
- `_detect_navigation_intent(user_input)`: Detect simple navigation phrases
- `handle_navigation()`: Show question list and handle user selection

## Validation System

### validator.py Functions

**Main Validation Function**
```python
def validate_answer(q_def: Dict[str, Any], reply: str) -> Tuple[bool, Any]
```
- Validates user input against question definition
- Returns (success_boolean, parsed_value_or_error_message)
- Handles type conversion and format validation

**Type-Specific Parsers**
- `_parse_date(s)`: Parse date strings using dateutil
- `_parse_time(s)`: Parse time with format validation
- `_parse_number(s)`: Extract numbers from various formats
- `_parse_bool(s)`: Parse yes/no responses
- `_parse_choice(s, q_def, multi)`: Handle single/multiple choice
- `_parse_group(reply, q_def)`: Parse JSON group responses
- `_parse_repeat_group(reply, q_def)`: Parse JSON repeat group arrays
- `_parse_table(reply, q_def)`: Parse tabular data

**Advanced Features**
- **Flexible Number Parsing**: Accepts "30", "30 km/h", "thirty"
- **Choice Normalization**: Handles case variations, partial matches
- **Other Specifications**: Supports custom "other" values
- **Text Normalization**: Standardizes punctuation and spacing

## Workflow States and Transitions

### State Diagram

```
START → start_form → ask_question → get_user_input → check_navigation
                          ↑              ↓                    ↓
                          └─── retry ←───┤                   ↓
                                        ↓                    ↓
                     ┌─ advance_to_next ←─ validate_input ←─ ┤
                     │         ↓                            ↓
                     │   ask_question                 handle_navigation
                     │                                      ↓
                     │                                ask_question
                     │
                     ├─ handle_followup ← followup
                     │         ↓
                     │   (next_question/complete)
                     │
                     ├─ handle_group_question ← group/group_complete
                     │         ↓
                     │   (continue_group/next_question/complete)
                     │
                     ├─ handle_repeat_group ← repeat_group/repeat_group_complete
                     │         ↓
                     │   (continue_repeat/ask_for_more/next_question/complete)
                     │
                     └─ complete_form ← complete → END
```

### Routing Logic

After user input, the system first checks for navigation intent, then routes based on:

1. **Reply Change Request**: User wants to edit a previous answer
2. **Validation Failure**: Retry current question  
3. **In Repeat Group**: Continue with next field or instance
4. **In Group**: Continue with next field or complete group
5. **Boolean with Follow-up**: Handle conditional questions
6. **Last Question**: Complete form
7. **Default**: Advance to next question

## Reply Editing

### Simple Navigation Commands

Users can edit previous replies using simple commands:
- "change reply"
- "change answer" 
- "edit reply"
- "edit answer"
- "modify reply"
- "modify answer"

### Reply Editing Process

1. **Command Detection**: System detects edit request in user input
2. **Question Selection**: Shows numbered list of completed questions
3. **User Choice**: User selects question number or types 'cancel'
4. **Question Navigation**: Jumps to selected question for re-answering
5. **Return to Flow**: After new answer, continues normal progression

### Reply Editing Examples

```
👤 Your answer: change reply
🔄 Which question would you like to change?
Here are the questions you've already answered:
--------------------------------------------------
1. What was the date of the accident?
   Current answer: 2025-06-12

2. What was the weather like?
   Current answer: Clear

3. How many vehicles were involved?
   Current answer: 2

Type the number of the question you want to change, or 'cancel' to continue:

👤 Your choice: 2
🔄 Editing: What was the weather like?
Current answer: Clear
Please provide your new answer:

👤 Your answer: Rain
✅ Answer recorded: Rain
(Returns to normal flow...)
```

## Usage Examples

### Basic Usage (Interactive Mode)

```python
from bot_naive import FormWorkflow

# Initialize with default questions file
workflow = FormWorkflow()

# Run interactively in terminal
workflow.run_form()
```

### Web Service Mode with UI Components

```python
# Initialize in web mode with UI components enabled
workflow = FormWorkflow(interactive=False, web_ui_enabled=True)

# Compile the graph
graph = workflow.compile_graph()

# Process user input
config = {"configurable": {"thread_id": "user_session_123"}}
result = graph.invoke({"messages": [HumanMessage(content="user_response")]}, config)
```

### Web Service Mode (Text Only)

```python
# Initialize in non-interactive mode without UI components
workflow = FormWorkflow(interactive=False, web_ui_enabled=False)

# Compile the graph
graph = workflow.compile_graph()

# Process user input
config = {"configurable": {"thread_id": "user_session_123"}}
result = graph.invoke({"messages": [HumanMessage(content="user_response")]}, config)
```

### Custom Questions File

```python
workflow = FormWorkflow(questions_file="/path/to/custom_questions.json", web_ui_enabled=True)
workflow.run_form()
```

### UI Component Usage in Web Interface

When `web_ui_enabled=True`, the bot will generate JSON messages containing UI components:

```json
{
  "sender": "bot",
  "text": "❓ What was the weather like at the time of the accident?\n\nYou can click one option below, or type your answer:\n\nOptions:\n  1. Clear\n  2. Overcast\n  3. Rain\n  4. Snow",
  "ui_component": {
    "type": "clickable_choice",
    "question_id": "weather_conditions",
    "question_text": "What was the weather like at the time of the accident?",
    "options": ["Clear", "Overcast", "Rain", "Snow"],
    "allow_multiple": false,
    "allow_other": true,
    "instructions": "Click one option below: (Select 'Other' and specify if needed)"
  }
}
```

Frontend can parse the `ui_component` to render clickable buttons while still displaying the text for accessibility.

### Handling UI Responses

UI responses are sent as JSON:

```json
{
  "type": "choice_selection",
  "selected_options": ["Rain"],
  "other_text": ""
}
```

The bot automatically parses these and validates them like regular text input.

### Reply Editing During Form Completion

```python
# User can edit replies at any time during form completion
workflow = FormWorkflow()

# Example interaction:
# Question: What was the weather like?
# User: Clear
# 
# Question: How many vehicles were involved? 
# User: change reply
# System: Shows list of completed questions...
# User: 1
# System: Editing weather question...
# User: Rainy
# System: Continuing where we left off...
```

## Question Definition Format

### Basic Question Structure

```json
{
  "id": "unique_question_id",
  "question": "What is your question?",
  "type": "text|number|date|time|boolean|single_choice|multiple_choice",
  "gold_standard": "expected_answer_for_testing"
}
```

### Choice Questions

```json
{
  "id": "weather",
  "question": "What was the weather?",
  "type": "single_choice",
  "options": ["Clear", "Rain", "Snow", "Other"],
  "other_specify": true,
  "gold_standard": {
    "choice": "Rain",
    "other": null
  }
}
```

### Group Questions

```json
{
  "id": "road_conditions",
  "question": "Road and traffic details",
  "type": "group",
  "fields": [
    {
      "id": "surface",
      "question": "Road surface?",
      "type": "single_choice",
      "options": ["Dry", "Wet", "Ice"]
    }
  ],
  "gold_standard": {
    "surface": "Wet"
  }
}
```

### Repeat Group Questions

```json
{
  "id": "vehicles",
  "question": "Vehicle details",
  "type": "repeat_group",
  "fields": [
    {
      "id": "make_model",
      "question": "Make and model?",
      "type": "text"
    }
  ],
  "gold_standard": [
    {"make_model": "Toyota Camry"},
    {"make_model": "Honda Civic"}
  ]
}
```

### Follow-up Questions

```json
{
  "id": "any_injuries",
  "question": "Any injuries?",
  "type": "boolean",
  "gold_standard": true,
  "followup_if_yes": {
    "id": "injury_details",
    "question": "Describe injuries",
    "type": "text",
    "gold_standard": "Minor cuts"
  }
}
```

## Error Handling

### Validation Errors

The system provides specific error messages for different validation failures:

- **Invalid Format**: "Invalid time format. Please use HH:MM format"
- **Invalid Choice**: "\"xyz\" not a valid option"
- **Missing Required**: "Please specify what 'other' option you mean"
- **Type Mismatch**: "Expected yes/no or true/false"

### Retry Logic

- Failed validations increment `retry_count`
- Error messages stored in `last_error`
- System prompts user to try again with guidance
- No hard limit on retries (allows persistent correction)

### Exception Handling

- File not found errors for missing questions.json
- JSON parsing errors for malformed question definitions
- Graceful handling of keyboard interrupts
- State preservation on unexpected errors

## Configuration Options

### Interactive Mode
- **True**: Runs in terminal with user input prompts
- **False**: Web service mode, pauses for external input

### Questions File
- Default: `../questionnaire/questions.json`
- Custom: Any valid JSON file path
- Format: Must follow the question schema

### Graph Visualization
- Automatically generates `form_workflow_graph.png`
- Shows workflow structure and state transitions
- Useful for debugging and documentation

## Output Format

### Completed Form JSON

```json
{
  "form_title": "Simplified International Crash Report Form",
  "completion_date": "2025-08-06",
  "responses": {
    "date_of_accident": "2025-06-12",
    "time_of_accident": "14:35:00",
    "location_of_accident": "123 Main St, Springfield",
    "vehicles": [
      {
        "vehicle_type_make_model": "Sedan / Toyota / Camry",
        "licence_plate": "ABC-1234",
        "pre_crash_manoeuvre": "Turning-Left"
      }
    ]
  }
}
```

## Integration Points

### Backend Integration
- Can be imported into Flask applications
- Supports session-based state management
- Compatible with database storage systems

### Frontend Integration
- Web mode supports REST API integration
- State can be serialized/deserialized
- Supports real-time progress tracking

## Testing

### Test Files Location
Located in `../tests/` directory:
- `test_bot.py`: Basic bot functionality
- `test_integration.py`: End-to-end testing
- `comprehensive_test.py`: Full form completion tests

### Gold Standard Validation
- Each question includes `gold_standard` expected answers
- Enables automated testing of parsing logic
- Validates complete form workflows

## Performance Considerations

### Memory Usage
- State maintained in memory during session
- LangGraph checkpointing for persistence
- Suitable for concurrent users with session isolation

### Scalability
- Stateless between sessions
- Can be deployed with multiple instances
- Database integration recommended for production

## Known Limitations

1. **Single Language**: Currently English-only
2. **Linear Flow**: Doesn't support complex branching workflows beyond reply editing
3. **Limited Validation**: Basic type checking only
4. **Session Dependency**: Requires session state maintenance
5. **Simple Commands**: Reply editing requires exact command phrases

## Future Enhancements

1. **Multi-language Support**: Internationalization capabilities
2. **Complex Branching**: Conditional workflow paths
3. **Rich Validation**: Cross-field validation rules
4. **Progress Saving**: Ability to resume incomplete forms
5. **Dynamic Questions**: Runtime question generation
6. **Accessibility**: Screen reader and keyboard navigation support
7. **Enhanced Navigation**: Navigation within complex group/repeat group questions
8. **Smart Question Suggestions**: AI-powered navigation assistance

## Example: Reply Editing in Action

Here's what the simplified reply editing feature looks like in practice:

```
📋 Question 3/8
----------------------------------------
❓ What was the weather like at the time of the accident?
Options:
  1. Clear
  2. Overcast
  3. Rain
  4. Snow

👤 Your answer: Clear
✅ Answer recorded: Clear

📋 Question 4/8
----------------------------------------
❓ How many vehicles were involved in the accident?
Options:
  1. 1
  2. 2
  3. 3
  4. Other

💡 To change a previous answer, type 'change reply'

👤 Your answer: change reply
 Which question would you like to change?
Here are the questions you've already answered:
--------------------------------------------------
1. What was the date of the accident?
   Current answer: 2025-06-12

2. What time did the accident occur?
   Current answer: 14:35:00

3. What was the weather like at the time of the accident?
   Current answer: Clear

Type the number of the question you want to change, or 'cancel' to continue:

👤 Your choice: 3
🔄 Editing: What was the weather like at the time of the accident?
Current answer: Clear
Please provide your new answer:

👤 Your answer: Rain
✅ Answer recorded: Rain

📋 Question 4/8
----------------------------------------
❓ How many vehicles were involved in the accident?
(Continuing where we left off...)
```

## Troubleshooting

### Common Issues

**"Questions file not found"**
- Verify the questions.json file exists
- Check file path in FormWorkflow initialization

**"Invalid JSON in questions.json"**
- Validate JSON syntax using a JSON validator
- Check for trailing commas or quotes

**"Validation keeps failing"**
- Check expected input format in error messages
- Review question type and options
- Try different input variations

**"Graph visualization fails"**
- Install required graphviz dependencies
- Check write permissions in current directory

### Debug Mode

Enable detailed logging by modifying the workflow:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

workflow = FormWorkflow(questions_file="questions.json")
```

## Dependencies

### Required Packages
- `langgraph`: Workflow orchestration
- `langchain-core`: Message handling
- `dateutil`: Date/time parsing
- `json`: Data serialization
- `re`: Regular expressions
- `typing`: Type annotations

### Optional Packages
- `graphviz`: Workflow visualization
- `flask`: Web service integration
- `pytest`: Testing framework

## Contributing

When extending the bot:

1. Add new question types to `validator.py`
2. Update `FormState` if new state fields needed
3. Extend routing logic for new workflow paths
4. Add comprehensive tests for new features
5. Update documentation with examples

## License

This component is part of the WebWOz project and follows the project's licensing terms.
