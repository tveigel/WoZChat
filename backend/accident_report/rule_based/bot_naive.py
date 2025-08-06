import json
from typing import Annotated, Dict, Any, Optional, List
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from typing import Literal
try:
    from .validator import validate_answer
except ImportError:
    from validator import validate_answer


class FormState(TypedDict):
    messages: Annotated[list, add_messages]
    current_question_id: str
    current_question_index: int
    form_data: Dict[str, Any]
    questions_completed: List[str]
    retry_count: int
    last_error: Optional[str]
    form_complete: bool
    validation_success: bool
    # For handling group questions
    current_group_question: Optional[Dict[str, Any]]
    current_group_field_index: int
    group_data: Dict[str, Any]
    # For handling repeat_group questions (like vehicle details)
    current_repeat_group_question: Optional[Dict[str, Any]]
    current_repeat_instance: int  # Which instance of the repeat group (0, 1, 2...)
    current_repeat_field_index: int  # Which field within current instance
    repeat_group_data: List[Dict[str, Any]]  # List of completed instances
    current_instance_data: Dict[str, Any]  # Data for current instance being filled


class FormWorkflow:
    def __init__(self, questions_file: str = "questions.json", *, interactive: bool = True):
        """Initialize the form workflow with questions from JSON file."""
        with open(questions_file, 'r') as f:
            self.questions_data = json.load(f)
        self.questions = self.questions_data["questions"]
        self.interactive = interactive
        self.graph_builder = StateGraph(FormState)
        self.memory = InMemorySaver()
        self._build_graph()
        
    def _build_graph(self):
        """Build the LangGraph workflow."""
        # Add nodes
        self.graph_builder.add_node("start_form", self.start_form)
        self.graph_builder.add_node("ask_question", self.ask_question)
        self.graph_builder.add_node("get_user_input", 
                                   self.get_user_input if self.interactive else self.noop_input)
        self.graph_builder.add_node("validate_input", self.validate_input)
        self.graph_builder.add_node("advance_to_next", self.advance_to_next)
        self.graph_builder.add_node("handle_followup", self.handle_followup)
        self.graph_builder.add_node("handle_group_question", self.handle_group_question)
        self.graph_builder.add_node("handle_repeat_group", self.handle_repeat_group)
        self.graph_builder.add_node("complete_form", self.complete_form)
        
        # Add edges
        self.graph_builder.add_edge(START, "start_form")
        self.graph_builder.add_edge("start_form", "ask_question")
        
        # In interactive mode: ask_question -> get_user_input -> validate_input
        # In web mode: ask_question -> END (pause and wait for external input)
        if self.interactive:
            self.graph_builder.add_edge("ask_question", "get_user_input")
            self.graph_builder.add_edge("get_user_input", "validate_input")
        # In web mode, we'll manually resume from validate_input when we get user input
        
        self.graph_builder.add_edge("advance_to_next", "ask_question")
        self.graph_builder.add_edge("handle_group_question", "ask_question")
        self.graph_builder.add_edge("handle_repeat_group", "ask_question")
        
        # Add conditional edges
        self.graph_builder.add_conditional_edges(
            "validate_input",
            self.route_after_validation,
            {
                "retry": "ask_question",
                "next_question": "advance_to_next", 
                "followup": "handle_followup",
                "group": "handle_group_question",
                "group_complete": "handle_group_question",
                "repeat_group": "handle_repeat_group",
                "repeat_group_complete": "handle_repeat_group",
                "complete": "complete_form"
            }
        )
        
        self.graph_builder.add_conditional_edges(
            "handle_followup",
            self.route_after_followup,
            {
                "next_question": "advance_to_next",
                "complete": "complete_form"
            }
        )
        
        self.graph_builder.add_conditional_edges(
            "handle_group_question",
            self.route_after_group,
            {
                "next_question": "advance_to_next",
                "continue_group": "ask_question",
                "complete": "complete_form"
            }
        )
        
        self.graph_builder.add_conditional_edges(
            "handle_repeat_group",
            self.route_after_repeat_group,
            {
                "next_question": "advance_to_next",
                "continue_repeat": "ask_question",
                "ask_for_more": "ask_question", 
                "complete": "complete_form"
            }
        )
        
        self.graph_builder.add_edge("complete_form", END)
        
    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get question definition by ID."""
        # First check main questions
        for q in self.questions:
            if q["id"] == question_id:
                return q
        
        # Then check follow-up questions
        return self.get_followup_question_by_id(question_id)
    
    def get_next_question(self, current_index: int) -> Optional[Dict[str, Any]]:
        """Get the next question in sequence."""
        if current_index + 1 < len(self.questions):
            return self.questions[current_index + 1]
        return None
    
    def noop_input(self, state: FormState) -> FormState:
        """Web mode: do NOT read from stdin, just pause."""
        return state
    
    def start_form(self, state: FormState) -> FormState:
        """Initialize the form session."""
        print(f"\n🏁 Welcome to the {self.questions_data['title']}")
        print("=" * 60)
        print("I'll guide you through filling out this form step by step.")
        print("Please answer each question as accurately as possible.\n")
        
        return {
            "current_question_id": self.questions[0]["id"],
            "current_question_index": 0,
            "form_data": {},
            "questions_completed": [],
            "retry_count": 0,
            "last_error": None,
            "form_complete": False,
            "validation_success": False,
            "current_group_question": None,
            "current_group_field_index": 0,
            "group_data": {},
            "current_repeat_group_question": None,
            "current_repeat_instance": 0,
            "current_repeat_field_index": 0,
            "repeat_group_data": [],
            "current_instance_data": {}
        }
    
    def ask_question(self, state: FormState) -> FormState:
        """Display the current question to the user."""
        # Check if we're in the middle of a repeat group question
        if state.get("current_repeat_group_question"):
            repeat_group = state["current_repeat_group_question"]
            instance_index = state.get("current_repeat_instance", 0)
            field_index = state.get("current_repeat_field_index", 0)
            
            if field_index < len(repeat_group["fields"]):
                current_field = repeat_group["fields"][field_index]
                
                # Show progress for repeat group questions
                progress = len(state["questions_completed"])
                total = len(self.questions)
                instance_progress = f" (Vehicle {instance_index + 1}, part {field_index + 1}/{len(repeat_group['fields'])})"
                print(f"\n📋 Question {progress + 1}/{total}{instance_progress}")
                print("-" * 40)
                
                # Display retry message if needed
                if state["retry_count"] > 0 and state["last_error"]:
                    print(f"❌ {state['last_error']}")
                    print("Let me ask that again...\n")
                
                print(f"❓ Vehicle {instance_index + 1} - {current_field['question']}")
                print(f"   (Please provide details for just Vehicle {instance_index + 1})")
                
                # Show format hints and options
                if current_field["type"] == "text":
                    if "type, make, and model" in current_field['question'].lower():
                        print("   (Example: 'Sedan / Toyota / Camry' or 'SUV / Honda / CR-V')")
                    elif "licence plate" in current_field['question'].lower():
                        print("   (Example: 'ABC-1234' or 'XYZ-5678')")
                    elif "damage" in current_field['question'].lower():
                        print("   (Example: 'Front-left fender dented' or 'Rear bumper scratched')")
                elif current_field["type"] == "number":
                    if "speed" in current_field['question'].lower():
                        print("   (Example: 30, 45, 60 - just the number in km/h)")
                
                # Show options for choice questions
                if current_field["type"] in ["single_choice", "multiple_choice"]:
                    print("Options:")
                    for i, option in enumerate(current_field["options"], 1):
                        print(f"  {i}. {option}")
                    if current_field.get("other_specify"):
                        print("  (You can also specify 'Other' with details)")
                    if current_field["type"] == "multiple_choice":
                        print("  (You can select multiple options separated by commas)")
                        
                return state
        
        # Check if we're in the middle of a group question
        elif state.get("current_group_question") and state.get("current_group_field_index", 0) < len(state["current_group_question"]["fields"]):
            # We're asking a sub-question of a group
            group_question = state["current_group_question"]
            field_index = state["current_group_field_index"]
            current_field = group_question["fields"][field_index]
            
            # Show progress for group questions
            progress = len(state["questions_completed"])
            total = len(self.questions)
            group_progress = f" (part {field_index + 1}/{len(group_question['fields'])})"
            print(f"\n📋 Question {progress + 1}/{total}{group_progress}")
            print("-" * 40)
            
            # Display retry message if needed
            if state["retry_count"] > 0 and state["last_error"]:
                print(f"❌ {state['last_error']}")
                print("Let me ask that again...\n")
                
            print(f"❓ {current_field['question']}")
            
            # Show options for choice questions
            if current_field["type"] in ["single_choice", "multiple_choice"]:
                print("Options:")
                for i, option in enumerate(current_field["options"], 1):
                    print(f"  {i}. {option}")
                if current_field.get("other_specify"):
                    print("  (You can also specify 'Other' with details)")
                if current_field["type"] == "multiple_choice":
                    print("  (You can select multiple options separated by commas)")
        else:
            # Regular question or start of group/repeat_group question
            question = self.get_question_by_id(state["current_question_id"])
            if not question:
                return state
            
            # Show progress
            progress = len(state["questions_completed"])
            total = len(self.questions)
            print(f"\n📋 Question {progress + 1}/{total}")
            print("-" * 40)
            
            # Display retry message if needed
            if state["retry_count"] > 0 and state["last_error"]:
                print(f"❌ {state['last_error']}")
                print("Let me ask that again...\n")
            
            # For repeat_group questions, show special instructions
            if question["type"] == "repeat_group":
                print(f"❓ {question['question']}")
                print(f"💡 I'll ask you about each vehicle separately, one question at a time.")
                print(f"📝 Let's start with Vehicle 1:")
                # Start with the first field of the first instance
                first_field = question["fields"][0]
                print(f"\n❓ Vehicle 1 - {first_field['question']}")
                print(f"   (Please provide details for just this one vehicle)")
                
                # Show options for choice questions
                if first_field["type"] in ["single_choice", "multiple_choice"]:
                    print("Options:")
                    for i, option in enumerate(first_field["options"], 1):
                        print(f"  {i}. {option}")
                    if first_field.get("other_specify"):
                        print("  (You can also specify 'Other' with details)")
                    if first_field["type"] == "multiple_choice":
                        print("  (You can select multiple options separated by commas)")
                elif first_field["type"] == "text":
                    print("   (Example: 'Sedan / Toyota / Camry' or 'SUV / Honda / CR-V')")
                elif first_field["type"] == "number":
                    print("   (Please enter a number)")
                elif first_field["type"] == "date":
                    print("   (Format: YYYY-MM-DD, e.g., 2025-06-12)")
                elif first_field["type"] == "time":
                    print("   (Format: HH:MM, e.g., 14:35)")
            
            # Check if this is a group question - if so, start with first field
            elif question["type"] == "group":
                print(f"❓ {question['question']}")
                print(f"💡 I'll ask you each part of this question step by step.")
                # Start with the first field
                first_field = question["fields"][0]
                print(f"\n❓ {first_field['question']}")
                
                # Show options for choice questions
                if first_field["type"] in ["single_choice", "multiple_choice"]:
                    print("Options:")
                    for i, option in enumerate(first_field["options"], 1):
                        print(f"  {i}. {option}")
                    if first_field.get("other_specify"):
                        print("  (You can also specify 'Other' with details)")
                    if first_field["type"] == "multiple_choice":
                        print("  (You can select multiple options separated by commas)")
            else:
                # Regular question
                print(f"❓ {question['question']}")
                
                # Show options for choice questions
                if question["type"] in ["single_choice", "multiple_choice"]:
                    print("Options:")
                    for i, option in enumerate(question["options"], 1):
                        print(f"  {i}. {option}")
                    if question.get("other_specify"):
                        print("  (You can also specify 'Other' with details)")
                    if question["type"] == "multiple_choice":
                        print("  (You can select multiple options separated by commas)")
                
                # Show format hints for other question types
                elif question["type"] == "date":
                    print("(Format: YYYY-MM-DD, e.g., 2025-06-12)")
                elif question["type"] == "time":
                    print("(Format: HH:MM, e.g., 14:35)")
                elif question["type"] == "number":
                    print("(Please enter a number)")
                elif question["type"] == "boolean":
                    print("(Please answer: yes/no, true/false, or 1/0)")
        
        return state
    
    def get_user_input(self, state: FormState) -> FormState:
        """Get input from the user."""
        if not self.interactive:
            # Should never be reached, but guard anyway
            raise RuntimeError("get_user_input called in non-interactive mode")
        
        user_response = input("\n👤 Your answer: ").strip()
        
        return {
            "messages": state["messages"] + [HumanMessage(content=user_response)]
        }
    
    def advance_to_next(self, state: FormState) -> FormState:
        """Advance to the next question."""
        next_question = self.get_next_question(state["current_question_index"])
        if next_question:
            # Create a complete new state update without conflicting keys
            return {
                **{k: v for k, v in state.items() if k not in [
                    "current_question_id", "current_question_index", "current_group_question",
                    "current_group_field_index", "group_data", "current_repeat_group_question",
                    "current_repeat_instance", "current_repeat_field_index", "repeat_group_data",
                    "current_instance_data", "retry_count", "last_error", "validation_success"
                ]},
                "current_question_id": next_question["id"],
                "current_question_index": state["current_question_index"] + 1,
                "current_group_question": None,
                "current_group_field_index": 0,
                "group_data": {},
                "current_repeat_group_question": None,
                "current_repeat_instance": 0,
                "current_repeat_field_index": 0,
                "repeat_group_data": [],
                "current_instance_data": {},
                "retry_count": 0,
                "last_error": None,
                "validation_success": False
            }
        return state
    
    def validate_input(self, state: FormState) -> FormState:
        """Validate the user's input against the question definition."""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]
        user_input = last_message.content
        
        # Check if we're in a repeat_group question
        if state.get("current_repeat_group_question"):
            repeat_group = state["current_repeat_group_question"]
            instance_index = state.get("current_repeat_instance", 0)
            field_index = state.get("current_repeat_field_index", 0)
            
            if field_index < len(repeat_group["fields"]):
                current_field = repeat_group["fields"][field_index]
                
                # Validate the input
                is_valid, result = validate_answer(current_field, user_input)
                
                if is_valid:
                    print(f"✅ Answer recorded: {result}")
                    
                    # Store the field answer in current_instance_data
                    new_instance_data = state.get("current_instance_data", {}).copy()
                    new_instance_data[current_field["id"]] = result
                    
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "current_instance_data", "retry_count", "last_error", "validation_success"
                        ]},
                        "current_instance_data": new_instance_data,
                        "retry_count": 0,
                        "last_error": None,
                        "validation_success": True
                    }
                else:
                    error_msg = f"Invalid input: {result}. Please try again."
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "retry_count", "last_error", "validation_success"
                        ]},
                        "retry_count": state["retry_count"] + 1,
                        "last_error": error_msg,
                        "validation_success": False
                    }
        
        # Check if we're in a group question
        elif state.get("current_group_question") and state.get("current_group_field_index", 0) < len(state["current_group_question"]["fields"]):
            # We're validating a field within a group question
            group_question = state["current_group_question"]
            field_index = state["current_group_field_index"]
            question_def = group_question["fields"][field_index]
            field_id = question_def["id"]
            
            # Validate the input
            is_valid, result = validate_answer(question_def, user_input)
            
            if is_valid:
                print(f"✅ Answer recorded: {result}")
                
                # Store the field answer in group_data
                new_group_data = state["group_data"].copy()
                new_group_data[field_id] = result
                
                return {
                    **{k: v for k, v in state.items() if k not in [
                        "group_data", "retry_count", "last_error", "validation_success"
                    ]},
                    "group_data": new_group_data,
                    "retry_count": 0,
                    "last_error": None,
                    "validation_success": True
                }
            else:
                error_msg = f"Invalid input: {result}. Please try again."
                return {
                    **{k: v for k, v in state.items() if k not in [
                        "retry_count", "last_error", "validation_success"
                    ]},
                    "retry_count": state["retry_count"] + 1,
                    "last_error": error_msg,
                    "validation_success": False
                }
        else:
            # Regular question validation or first time group/repeat_group question
            question_def = self.get_question_by_id(state["current_question_id"])
            if not question_def:
                return state
            
            # If this is a repeat_group question and we haven't initialized it yet
            if question_def["type"] == "repeat_group" and not state.get("current_repeat_group_question"):
                # Initialize repeat_group question with first field of first instance
                first_field = question_def["fields"][0]
                
                # Validate against the first field
                is_valid, result = validate_answer(first_field, user_input)
                
                if is_valid:
                    print(f"✅ Answer recorded: {result}")
                    # Initialize repeat group data with first field result
                    new_instance_data = {first_field["id"]: result}
                    
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "current_repeat_group_question", "current_repeat_instance",
                            "current_repeat_field_index", "repeat_group_data", "current_instance_data",
                            "retry_count", "last_error", "validation_success"
                        ]},
                        "current_repeat_group_question": question_def,
                        "current_repeat_instance": 0,
                        "current_repeat_field_index": 0,
                        "repeat_group_data": [],
                        "current_instance_data": new_instance_data,
                        "retry_count": 0,
                        "last_error": None,
                        "validation_success": True
                    }
                else:
                    error_msg = f"Invalid input: {result}. Please try again."
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "current_repeat_group_question", "current_repeat_instance",
                            "current_repeat_field_index", "repeat_group_data", "current_instance_data",
                            "retry_count", "last_error", "validation_success"
                        ]},
                        "current_repeat_group_question": question_def,
                        "current_repeat_instance": 0,
                        "current_repeat_field_index": 0,
                        "repeat_group_data": [],
                        "current_instance_data": {},
                        "retry_count": state["retry_count"] + 1,
                        "last_error": error_msg,
                        "validation_success": False
                    }
            
            # If this is a group question and we haven't initialized it yet
            elif question_def["type"] == "group" and not state.get("current_group_question"):
                # Initialize group question with first field
                first_field = question_def["fields"][0]
                
                # Validate against the first field
                is_valid, result = validate_answer(first_field, user_input)
                
                if is_valid:
                    print(f"✅ Answer recorded: {result}")
                    # Initialize group data with first field result
                    new_group_data = {first_field["id"]: result}
                    
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "current_group_question", "current_group_field_index", "group_data",
                            "retry_count", "last_error", "validation_success"
                        ]},
                        "current_group_question": question_def,
                        "current_group_field_index": 0,
                        "group_data": new_group_data,
                        "retry_count": 0,
                        "last_error": None,
                        "validation_success": True
                    }
                else:
                    error_msg = f"Invalid input: {result}. Please try again."
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "current_group_question", "current_group_field_index", "group_data",
                            "retry_count", "last_error", "validation_success"
                        ]},
                        "current_group_question": question_def,
                        "current_group_field_index": 0,
                        "group_data": {},
                        "retry_count": state["retry_count"] + 1,
                        "last_error": error_msg,
                        "validation_success": False
                    }
            else:
                # Regular question - validate and store directly
                is_valid, result = validate_answer(question_def, user_input)
                
                if is_valid:
                    print(f"✅ Answer recorded: {result}")
                    
                    new_form_data = state["form_data"].copy()
                    new_form_data[state["current_question_id"]] = result
                    
                    new_completed = state["questions_completed"].copy()
                    if state["current_question_id"] not in new_completed:
                        new_completed.append(state["current_question_id"])
                    
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "form_data", "questions_completed", "retry_count", "last_error", "validation_success"
                        ]},
                        "form_data": new_form_data,
                        "questions_completed": new_completed,
                        "retry_count": 0,
                        "last_error": None,
                        "validation_success": True
                    }
                else:
                    error_msg = f"Invalid input: {result}. Please try again."
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "retry_count", "last_error", "validation_success"
                        ]},
                        "retry_count": state["retry_count"] + 1,
                        "last_error": error_msg,
                        "validation_success": False
                    }
    
    def handle_followup(self, state: FormState) -> FormState:
        """Handle conditional followup questions."""
        current_question = self.get_question_by_id(state["current_question_id"])
        if not current_question:
            return state
            
        # Check if current question has followup logic
        if current_question["type"] == "boolean":
            user_answer = state["form_data"].get(state["current_question_id"])
            
            # Handle followup_if_yes
            if user_answer is True and "followup_if_yes" in current_question:
                followup = current_question["followup_if_yes"]
                print(f"\n🔄 Follow-up question needed...")
                
                # Store the follow-up question in form_data and mark as completed
                new_form_data = state["form_data"].copy()
                new_completed = state["questions_completed"].copy()
                
                # For now, we'll handle table type follow-ups by asking for a simple text description
                # since the current validator doesn't support table questions in a user-friendly way
                if followup["type"] == "table":
                    # Convert table question to a simple text question for now
                    simplified_question = {
                        "id": followup["id"],
                        "question": followup["question"] + "\n(Please provide details separated by commas or semicolons)",
                        "type": "multiline_text"
                    }
                    
                    # Create a complete new state update without conflicting keys
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "current_question_id", "retry_count", "last_error", "validation_success"
                        ]},
                        "current_question_id": followup["id"],
                        "retry_count": 0,
                        "last_error": None,
                        "validation_success": False  # Reset for followup question
                    }
                else:
                    # Regular follow-up question
                    return {
                        **{k: v for k, v in state.items() if k not in [
                            "current_question_id", "retry_count", "last_error", "validation_success"
                        ]},
                        "current_question_id": followup["id"],
                        "retry_count": 0,
                        "last_error": None,
                        "validation_success": False  # Reset for followup question
                    }
        
        return state
        
    def get_followup_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get a follow-up question definition by ID."""
        for main_question in self.questions:
            if "followup_if_yes" in main_question and main_question["followup_if_yes"]["id"] == question_id:
                followup = main_question["followup_if_yes"].copy()
                # Convert table questions to multiline_text for user-friendliness
                if followup["type"] == "table":
                    followup["type"] = "multiline_text"
                    followup["question"] = followup["question"] + "\n(Please provide details separated by commas or semicolons)"
                return followup
        return None
    
    def handle_group_question(self, state: FormState) -> FormState:
        """Handle progression through group question fields."""
        if not state.get("current_group_question"):
            return state
        
        group_question = state["current_group_question"]
        current_field_index = state.get("current_group_field_index", 0)
        
        # Move to next field in the group
        if current_field_index + 1 < len(group_question["fields"]):
            # Create a complete new state update without conflicting keys
            return {
                **{k: v for k, v in state.items() if k not in [
                    "current_group_field_index", "retry_count", "last_error", "validation_success"
                ]},
                "current_group_field_index": current_field_index + 1,
                "retry_count": 0,  # Reset retry count for new field
                "last_error": None,  # Clear any previous errors
                "validation_success": False  # Reset for next field
            }
        else:
            # We've completed all fields in the group
            # Store the complete group data
            new_form_data = state["form_data"].copy()
            new_form_data[state["current_question_id"]] = state["group_data"]
            
            new_completed = state["questions_completed"].copy()
            if state["current_question_id"] not in new_completed:
                new_completed.append(state["current_question_id"])
            
            print(f"✅ Group question completed: {state['group_data']}")
            
            # Create a complete new state update without conflicting keys
            return {
                **{k: v for k, v in state.items() if k not in [
                    "form_data", "questions_completed", "current_group_question",
                    "current_group_field_index", "group_data", "retry_count", "last_error", "validation_success"
                ]},
                "form_data": new_form_data,
                "questions_completed": new_completed,
                "current_group_question": None,
                "current_group_field_index": 0,
                "group_data": {},
                "retry_count": 0,
                "last_error": None,
                "validation_success": True  # Mark as successful to advance
            }
    
    def handle_repeat_group(self, state: FormState) -> FormState:
        """Handle progression through repeat group question fields and instances."""
        if not state.get("current_repeat_group_question"):
            return state
        
        repeat_group = state["current_repeat_group_question"]
        current_instance = state.get("current_repeat_instance", 0)
        current_field_index = state.get("current_repeat_field_index", 0)
        
        # Check if we need to move to the next field in the current instance
        if current_field_index + 1 < len(repeat_group["fields"]):
            # Move to next field in the current instance
            return {
                **{k: v for k, v in state.items() if k not in [
                    "current_repeat_field_index", "retry_count", "last_error", "validation_success"
                ]},
                "current_repeat_field_index": current_field_index + 1,
                "retry_count": 0,
                "last_error": None,
                "validation_success": False
            }
        else:
            # We've completed all fields for this instance
            # Add current instance data to the repeat group data
            new_repeat_group_data = state.get("repeat_group_data", []).copy()
            new_repeat_group_data.append(state.get("current_instance_data", {}))
            
            print(f"✅ Vehicle {current_instance + 1} details completed!")
            print(f"   📝 {state.get('current_instance_data', {})}")
            
            # Check if we should ask for more or finish
            # For now, let's assume they want to add exactly as many as specified in the number_of_vehicles question
            # But we'll also ask if they want to add more
            
            # For vehicle questions, we need to check how many vehicles they said were involved
            num_vehicles_answer = state["form_data"].get("number_of_vehicles_involved")
            expected_vehicles = 2  # Default
            
            if isinstance(num_vehicles_answer, dict) and "choice" in num_vehicles_answer:
                if num_vehicles_answer["choice"] in ["1", "2", "3"]:
                    expected_vehicles = int(num_vehicles_answer["choice"])
                else:
                    expected_vehicles = 2  # Default for "Other"
            elif isinstance(num_vehicles_answer, str):
                if num_vehicles_answer in ["1", "2", "3"]:
                    expected_vehicles = int(num_vehicles_answer)
            
            completed_vehicles = len(new_repeat_group_data)
            
            if completed_vehicles < expected_vehicles:
                # Start next vehicle
                print(f"\n� Great! Now let's get details for Vehicle {completed_vehicles + 1} of {expected_vehicles}...")
                print(f"─" * 50)
                
                return {
                    **{k: v for k, v in state.items() if k not in [
                        "repeat_group_data", "current_instance_data", "current_repeat_instance",
                        "current_repeat_field_index", "retry_count", "last_error", "validation_success"
                    ]},
                    "repeat_group_data": new_repeat_group_data,
                    "current_instance_data": {},
                    "current_repeat_instance": current_instance + 1,
                    "current_repeat_field_index": 0,
                    "retry_count": 0,
                    "last_error": None,
                    "validation_success": False  # Ready for next vehicle's first field
                }
            else:
                # We've completed all expected vehicles - finish the repeat group
                new_form_data = state["form_data"].copy()
                new_form_data[state["current_question_id"]] = new_repeat_group_data
                
                new_completed = state["questions_completed"].copy()
                if state["current_question_id"] not in new_completed:
                    new_completed.append(state["current_question_id"])
                
                print(f"✅ All vehicles completed! ({completed_vehicles} vehicles)")
                
                return {
                    **{k: v for k, v in state.items() if k not in [
                        "form_data", "questions_completed", "current_repeat_group_question",
                        "current_repeat_instance", "current_repeat_field_index", "repeat_group_data",
                        "current_instance_data", "retry_count", "last_error", "validation_success"
                    ]},
                    "form_data": new_form_data,
                    "questions_completed": new_completed,
                    "current_repeat_group_question": None,
                    "current_repeat_instance": 0,
                    "current_repeat_field_index": 0,
                    "repeat_group_data": [],
                    "current_instance_data": {},
                    "retry_count": 0,
                    "last_error": None,
                    "validation_success": True
                }
    
    def complete_form(self, state: FormState) -> FormState:
        """Complete the form and show summary."""
        print("\n🎉 Form completed successfully!")
        print("=" * 60)
        print("\n📋 Form Summary:")
        print("-" * 30)
        
        for question_id, answer in state["form_data"].items():
            question = self.get_question_by_id(question_id)
            if question:
                print(f"\n{question['question']}")
                if isinstance(answer, dict):
                    for key, value in answer.items():
                        print(f"  {key}: {value}")
                elif isinstance(answer, list):
                    for i, item in enumerate(answer, 1):
                        print(f"  {i}. {item}")
                else:
                    print(f"  Answer: {answer}")
        
        # Save to file
        output_file = "completed_form.json"
        with open(output_file, 'w') as f:
            json.dump({
                "form_title": self.questions_data["title"],
                "completion_date": "2025-08-06",  # Could use datetime.now()
                "responses": state["form_data"]
            }, f, indent=2, default=str)
        
        print(f"\n💾 Form data saved to: {output_file}")
        
        return {"form_complete": True}
    
    def route_after_validation(self, state: FormState) -> Literal["retry", "next_question", "followup", "group", "group_complete", "repeat_group", "repeat_group_complete", "complete"]:
        """Route after validation based on success/failure."""
        # Check if validation failed
        if not state.get("validation_success", False):
            return "retry"
        
        # Check if we're in a repeat_group question and need to continue with more fields or instances
        if state.get("current_repeat_group_question"):
            current_field_index = state.get("current_repeat_field_index", 0)
            repeat_group = state["current_repeat_group_question"]
            
            if current_field_index + 1 < len(repeat_group["fields"]):
                # More fields to go in this instance
                return "repeat_group"
            else:
                # This instance is complete, need to handle completion
                return "repeat_group_complete"
        
        # Check if we're in a group question and need to continue with more fields
        if state.get("current_group_question"):
            current_field_index = state.get("current_group_field_index", 0)
            group_question = state["current_group_question"]
            
            if current_field_index + 1 < len(group_question["fields"]):
                # More fields to go in this group
                return "group"
            else:
                # Group is complete, need to finalize it
                return "group_complete"
        
        current_question = self.get_question_by_id(state["current_question_id"])
        if not current_question:
            return "complete"
        
        # Check if we need a followup
        if current_question["type"] == "boolean":
            user_answer = state["form_data"].get(state["current_question_id"])
            if user_answer is True and "followup_if_yes" in current_question:
                return "followup"
        
        # Check if this is the last question
        if state["current_question_index"] >= len(self.questions) - 1:
            return "complete"
        
        return "next_question"
    
    def route_after_followup(self, state: FormState) -> Literal["next_question", "complete"]:
        """Route after handling followup questions."""
        # Check if there are more main questions
        next_question = self.get_next_question(state["current_question_index"])
        if next_question:
            return "next_question"
        return "complete"
    
    def route_after_group(self, state: FormState) -> Literal["next_question", "continue_group", "complete"]:
        """Route after handling group questions."""
        # If there's no current group question, we've completed it
        if not state.get("current_group_question"):
            # Check if this is the last question
            if state["current_question_index"] >= len(self.questions) - 1:
                return "complete"
            return "next_question"
        else:
            # Still in group, continue with next field
            return "continue_group"
    
    def route_after_repeat_group(self, state: FormState) -> Literal["next_question", "continue_repeat", "ask_for_more", "complete"]:
        """Route after handling repeat group questions."""
        # Check if we're still in a repeat group (continuing with more instances)
        if state.get("current_repeat_group_question"):
            return "continue_repeat"
        
        # If we're done with the repeat group, move to next question
        if state["current_question_index"] >= len(self.questions) - 1:
            return "complete"
        
        return "next_question"
    
    def compile_graph(self):
        """Compile and return the graph."""
        return self.graph_builder.compile(checkpointer=self.memory)
    
    def run_form(self):
        """Run the form workflow."""
        graph = self.compile_graph()
        
        # Generate and save graph visualization
        try:
            image_data = graph.get_graph().draw_mermaid_png()
            with open("form_workflow_graph.png", "wb") as f:
                f.write(image_data)
            print("📊 Workflow graph saved as 'form_workflow_graph.png'")
        except Exception as e:
            print(f"Could not generate graph visualization: {e}")
        
        # Run the workflow
        config = {"configurable": {"thread_id": "form_session_1"}, "recursion_limit": 100}
        
        try:
            # Stream the workflow step by step 
            for event in graph.stream({}, config=config):
                # Check if we've completed the form
                for node_name, node_state in event.items():
                    if node_state.get("form_complete"):
                        print("\n✅ Workflow completed successfully!")
                        return node_state
                        
        except KeyboardInterrupt:
            print("\n\n⏹️  Form interrupted by user. Your progress has been saved.")
            return None
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            # Try to get the current state for debugging
            try:
                current_state = graph.get_state(config)
                print(f"Current state: {current_state}")
            except:
                pass
            return None


def main():
    """Main function to run the form workflow."""
    try:
        workflow = FormWorkflow("questions.json")
        workflow.run_form()
    except FileNotFoundError:
        print("❌ Error: questions.json file not found!")
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in questions.json file!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()