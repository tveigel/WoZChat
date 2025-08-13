"""
Web-compatible rule-based bot integration for WebWOz system.
This module adapts the rule-based bot to work with Socket.IO communication.
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Add the accident_report directory to Python path for imports
BACKEND_DIR = Path(__file__).parent
ACCIDENT_REPORT_DIR = BACKEND_DIR / "accident_report"

# Add accident_report directory to path
sys.path.insert(0, str(ACCIDENT_REPORT_DIR))

# Also try adding the backend directory to the path for Docker compatibility
sys.path.insert(0, str(BACKEND_DIR))

try:
    # Try direct imports from rule_based directory
    from rule_based.validator import validate_answer
    from rule_based.bot_naive import FormState, FormWorkflow
    
    BOT_IMPORTS_SUCCESSFUL = True
    print("✅ Bot components imported successfully")
except ImportError as e:
    print(f"Warning: Could not import bot components from rule_based: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"ACCIDENT_REPORT_DIR: {ACCIDENT_REPORT_DIR}")
    print(f"ACCIDENT_REPORT_DIR exists: {ACCIDENT_REPORT_DIR.exists()}")
    
    if ACCIDENT_REPORT_DIR.exists():
        rule_based_dir = ACCIDENT_REPORT_DIR / "rule_based"
        print(f"rule_based dir exists: {rule_based_dir.exists()}")
        if rule_based_dir.exists():
            print(f"rule_based contents: {list(rule_based_dir.iterdir())}")
    
    # Try alternate import paths for Docker environment
    try:
        from backend.accident_report.rule_based.validator import validate_answer
        from backend.accident_report.rule_based.bot_naive import FormState, FormWorkflow
        BOT_IMPORTS_SUCCESSFUL = True
        print("✅ Bot components imported successfully (Docker path)")
    except ImportError as e2:
        print(f"Warning: Could not import bot components from backend path: {e2}")
        print("Bot functionality will be limited.")
        FormWorkflow = None
        validate_answer = None
        FormState = None
        BOT_IMPORTS_SUCCESSFUL = False

# Try to import AI bot components
try:
    from accident_report.LLM.rigid_AI_bot import AIBotWorkflow
    from langchain_core.messages import HumanMessage
    AI_BOT_IMPORTS_SUCCESSFUL = True
    print("✅ AI Bot components imported successfully")
except ImportError as e:
    print(f"Warning: Could not import AI bot components: {e}")
    try:
        from backend.accident_report.LLM.rigid_AI_bot import AIBotWorkflow
        from langchain_core.messages import HumanMessage
        AI_BOT_IMPORTS_SUCCESSFUL = True
        print("✅ AI Bot components imported successfully (Docker path)")
    except ImportError as e2:
        print(f"Warning: Could not import AI bot components from backend path: {e2}")
        AIBotWorkflow = None
        HumanMessage = None
        AI_BOT_IMPORTS_SUCCESSFUL = False


class WebBotSession:
    """Web-compatible bot session that handles Socket.IO communication."""
    
    def __init__(self, room_id: str, questions_file: str = None):
        self.room_id = room_id
        self.is_active = False
        self.current_state = None
        self.workflow = None
        self.graph = None
        self.config = {"configurable": {"thread_id": f"bot_session_{room_id}"}, "recursion_limit": 50}
        
        # Default questions file path
        if questions_file is None:
            questions_file = ACCIDENT_REPORT_DIR / "questionnaire" / "questions.json"
        
        self.questions_file = str(questions_file)
        
        # Initialize the workflow if possible
        if BOT_IMPORTS_SUCCESSFUL and FormWorkflow and os.path.exists(self.questions_file):
            try:
                self.workflow = FormWorkflow(self.questions_file, interactive=False, web_ui_enabled=True)
                self.graph = self.workflow.compile_graph()
                print(f"✅ Bot initialized for room {room_id}")
            except Exception as e:
                print(f"❌ Failed to initialize bot for room {room_id}: {e}")
                self.workflow = None
        else:
            if not BOT_IMPORTS_SUCCESSFUL:
                print(f"⚠️ Bot not available for room {room_id} (import failed)")
            elif not os.path.exists(self.questions_file):
                print(f"⚠️ Bot not available for room {room_id} (questions file not found)")
            else:
                print(f"⚠️ Bot not available for room {room_id} (missing dependencies)")
    
    def start(self) -> Optional[str]:
        """Start the bot session and return the initial message."""
        if not self.workflow or not self.graph:
            return "❌ Bot is not available. Please check the configuration."
        
        try:
            self.is_active = True
            # Initialize the bot state
            initial_state = {}
            
            # Run the workflow until it reaches ask_question (in web mode, this is where it ends)
            for event in self.graph.stream(initial_state, config=self.config):
                # In web mode, workflow should stop after ask_question
                pass
            
            # Get the current state after asking the first question
            current_state = self.graph.get_state(self.config)
            if current_state:
                self.current_state = current_state.values
                
                # Get the first question
                question_message = self._get_current_question()
                if question_message:
                    return f"🤖 **Accident Report Bot Activated**\n\n{question_message}"
            
            return "🤖 **Accident Report Bot Activated**\n\nHello! I'll help you fill out an accident report. Let me start with the first question..."
            
        except Exception as e:
            print(f"❌ Error starting bot session: {e}")
            import traceback
            traceback.print_exc()
            self.is_active = False
            return f"❌ Failed to start bot: {str(e)}"
    
    def process_message(self, user_message: str) -> Optional[str]:
        """Process a user message and return the bot's response."""
        if not self.is_active or not self.workflow or not self.graph:
            return None
        
        try:
            # Get current state
            current_state_obj = self.graph.get_state(self.config)
            if not current_state_obj or not current_state_obj.values:
                return "❌ Bot session lost. Please restart the bot."
            
            state_values = current_state_obj.values
            
            # Add user message to the state and create updated state for validation
            from langchain_core.messages import HumanMessage
            updated_state = {
                **state_values,
                "messages": state_values.get("messages", []) + [HumanMessage(content=user_message)]
            }
            
            # Manually run validate_input node
            new_state = self.workflow.validate_input(updated_state)
            
            # Update the graph state with the validation result
            self.graph.update_state(self.config, new_state)
            
            # Get the routing decision from validate_input
            route = self.workflow.route_after_validation(new_state)
            
            # Handle the routing decision
            if route == "retry":
                # Validation failed, re-ask the question
                ask_result = self.workflow.ask_question(new_state)
                self.graph.update_state(self.config, ask_result)
                self.current_state = ask_result  # Update current state
                response = self._get_current_response()
                return response
                
            elif route == "next_question":
                # Move to next question
                advance_result = self.workflow.advance_to_next(new_state)
                self.graph.update_state(self.config, advance_result)
                ask_result = self.workflow.ask_question(advance_result)
                self.graph.update_state(self.config, ask_result)
                self.current_state = ask_result  # Update current state
                response = self._get_current_response()
                return response
                
            elif route == "followup":
                # Handle followup question
                followup_result = self.workflow.handle_followup(new_state)
                self.graph.update_state(self.config, followup_result)
                ask_result = self.workflow.ask_question(followup_result)
                self.graph.update_state(self.config, ask_result)
                self.current_state = ask_result  # Update current state
                response = self._get_current_response()
                return response
                
            elif route == "group":
                # Continue with group question
                group_result = self.workflow.handle_group_question(new_state)
                self.graph.update_state(self.config, group_result)
                ask_result = self.workflow.ask_question(group_result)
                self.graph.update_state(self.config, ask_result)
                self.current_state = ask_result  # Update current state
                response = self._get_current_response()
                return response
                
            elif route == "group_complete":
                # Complete the group and move to next
                group_result = self.workflow.handle_group_question(new_state)
                self.graph.update_state(self.config, group_result)
                
                # Check if form is complete
                if group_result.get("current_question_index", 0) >= len(self.workflow.questions) - 1:
                    complete_result = self.workflow.complete_form(group_result)
                    self.graph.update_state(self.config, complete_result)
                    self.is_active = False
                    return self._generate_completion_message()
                else:
                    # Advance to next question
                    advance_result = self.workflow.advance_to_next(group_result)
                    self.graph.update_state(self.config, advance_result)
                    ask_result = self.workflow.ask_question(advance_result)
                    self.graph.update_state(self.config, ask_result)
                    self.current_state = ask_result  # Update current state
                    response = self._get_current_response()
                    return response
                    
            elif route == "repeat_group":
                # Continue with repeat group question
                repeat_result = self.workflow.handle_repeat_group(new_state)
                self.graph.update_state(self.config, repeat_result)
                ask_result = self.workflow.ask_question(repeat_result)
                self.graph.update_state(self.config, ask_result)
                self.current_state = ask_result  # Update current state
                response = self._get_current_response()
                return response
                
            elif route == "repeat_group_complete":
                # Complete the repeat group instance and handle next steps
                repeat_result = self.workflow.handle_repeat_group(new_state)
                self.graph.update_state(self.config, repeat_result)
                
                # Check if we're still in the repeat group (more vehicles to add)
                if repeat_result.get("current_repeat_group_question"):
                    # Continue with next vehicle
                    ask_result = self.workflow.ask_question(repeat_result)
                    self.graph.update_state(self.config, ask_result)
                    self.current_state = ask_result  # Update current state
                    response = self._get_current_response()
                    return response
                else:
                    # Repeat group is complete, check if form is complete
                    if repeat_result.get("current_question_index", 0) >= len(self.workflow.questions) - 1:
                        complete_result = self.workflow.complete_form(repeat_result)
                        self.graph.update_state(self.config, complete_result)
                        self.is_active = False
                        return self._generate_completion_message()
                    else:
                        # Advance to next question
                        advance_result = self.workflow.advance_to_next(repeat_result)
                        self.graph.update_state(self.config, advance_result)
                        ask_result = self.workflow.ask_question(advance_result)
                        self.graph.update_state(self.config, ask_result)
                        self.current_state = ask_result  # Update current state
                        response = self._get_current_response()
                        return response
                    
            elif route == "complete":
                # Form is complete
                complete_result = self.workflow.complete_form(new_state)
                self.graph.update_state(self.config, complete_result)
                self.is_active = False
                return self._generate_completion_message()
            
            return "❌ Something went wrong processing your response. Please try again."
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error: {str(e)}. Please try again or restart the bot."
    
    def stop(self) -> str:
        """Stop the bot session."""
        self.is_active = False
        return "🤖 **Bot Deactivated**\n\nThe accident report bot has been stopped. You can now chat normally with the wizard."
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot session status."""
        if not self.current_state:
            return {
                "active": self.is_active,
                "available": self.workflow is not None,
                "progress": "Not started"
            }
        
        total_questions = len(self.workflow.questions) if self.workflow else 0
        current_index = self.current_state.get("current_question_index", 0)
        completed_questions = len(self.current_state.get("questions_completed", []))
        
        # Use the improved progress calculation
        progress_text = self._calculate_progress()
        
        return {
            "active": self.is_active,
            "available": self.workflow is not None,
            "progress": progress_text,
            "current_question_index": current_index,
            "completed_main_questions": completed_questions,
            "total_main_questions": total_questions,
            "form_complete": self.current_state.get("form_complete", False)
        }
    
    def _get_current_question(self) -> Optional[str]:
        """Get the current question text."""
        if not self.current_state or not self.workflow:
            return None
        
        # Handle repeat group questions (like vehicle details)
        if self.current_state.get("current_repeat_group_question"):
            repeat_group = self.current_state["current_repeat_group_question"]
            instance_index = self.current_state.get("current_repeat_instance", 0)
            field_index = self.current_state.get("current_repeat_field_index", 0)
            
            if field_index < len(repeat_group["fields"]):
                field = repeat_group["fields"][field_index]
                
                # Create a user-friendly question format
                main_question = repeat_group["question"]
                field_question = field["question"]
                
                question_text = f"**{main_question}**\n\n"
                question_text += f"**Vehicle {instance_index + 1}:** {field_question}\n"
                question_text += f"*(Please provide details for just Vehicle {instance_index + 1})*\n"
                
                # Add examples for specific field types
                if field["type"] == "text":
                    if "type, make, and model" in field_question.lower():
                        question_text += "\n*Example: 'Sedan / Toyota / Camry' or 'SUV / Honda / CR-V'*"
                    elif "licence plate" in field_question.lower():
                        question_text += "\n*Example: 'ABC-1234' or 'XYZ-5678'*"
                    elif "damage" in field_question.lower():
                        question_text += "\n*Example: 'Front-left fender dented' or 'Rear bumper scratched'*"
                elif field["type"] == "number" and "speed" in field_question.lower():
                    question_text += "\n*Example: 30, 45, 60 (just the number in km/h)*"
                
                # Add choices for multiple choice questions
                if field["type"] in ["single_choice", "multiple_choice"]:
                    options = field.get("options", [])
                    if options:
                        choices_text = "\n".join([f"• {choice}" for choice in options])
                        question_text += f"\n\n**Options:**\n{choices_text}"
                    
                    if field.get("other_specify"):
                        question_text += "\n*(You can also specify 'Other' with details)*"
                    if field["type"] == "multiple_choice":
                        question_text += "\n*(You can select multiple options separated by commas)*"
                
                return question_text
        
        # Handle group questions
        elif self.current_state.get("current_group_question"):
            group_question = self.current_state["current_group_question"]
            field_index = self.current_state.get("current_group_field_index", 0)
            
            if field_index < len(group_question["fields"]):
                field = group_question["fields"][field_index]
                question_text = f"**{group_question['question']}**\n\n{field['question']}"
                
                # Add choices for multiple choice questions
                if field["type"] in ["single_choice", "multiple_choice"]:
                    options = field.get("options", [])
                    if options:
                        choices_text = "\n".join([f"• {choice}" for choice in options])
                        question_text += f"\n\n**Options:**\n{choices_text}"
                    
                    if field.get("other_specify"):
                        question_text += "\n*(You can also specify 'Other' with details)*"
                    if field["type"] == "multiple_choice":
                        question_text += "\n*(You can select multiple options separated by commas)*"
                
                return question_text
        
        # Regular questions
        else:
            question_id = self.current_state.get("current_question_id")
            if question_id:
                question = self.workflow.get_question_by_id(question_id)
                if question:
                    question_text = question["question"]
                    
                    # Special handling for repeat_group questions at start
                    if question["type"] == "repeat_group":
                        question_text += "\n\n*I'll ask you about each item separately, one question at a time.*"
                        first_field = question["fields"][0] if question["fields"] else None
                        if first_field:
                            question_text += f"\n\n**Item 1:** {first_field['question']}"
                            if first_field["type"] == "text":
                                question_text += "\n*Please provide details for just the first item*"
                    
                    # Special handling for group questions at start  
                    elif question["type"] == "group":
                        question_text += "\n\n*I'll ask you each part of this question step by step.*"
                        first_field = question["fields"][0] if question["fields"] else None
                        if first_field:
                            question_text += f"\n\n{first_field['question']}"
                    
                    # Add choices for multiple choice questions
                    elif question["type"] in ["single_choice", "multiple_choice"]:
                        options = question.get("options", [])
                        if options:
                            choices_text = "\n".join([f"• {choice}" for choice in options])
                            question_text += f"\n\n**Options:**\n{choices_text}"
                        
                        if question.get("other_specify"):
                            question_text += "\n*(You can also specify 'Other' with details)*"
                        if question["type"] == "multiple_choice":
                            question_text += "\n*(You can select multiple options separated by commas)*"
                    
                    # Add format hints for other question types
                    elif question["type"] == "date":
                        question_text += "\n*(Format: YYYY-MM-DD, e.g., 2025-06-12)*"
                    elif question["type"] == "time":
                        question_text += "\n*(Format: HH:MM, e.g., 14:35)*"
                    elif question["type"] == "number":
                        question_text += "\n*(Please enter a number)*"
                    elif question["type"] == "boolean":
                        question_text += "\n*(Please answer: yes/no, true/false, or 1/0)*"
                    elif question["type"] in ["text", "multiline_text"]:
                        question_text += "\n*(Please provide a detailed response)*"
                    
                    return question_text
        
        return None
    
    def _get_current_response(self) -> Optional[str]:
        """Generate response based on current state."""
        if not self.current_state:
            return None
        
        # Check if the last message is a UI message (JSON format)
        if self.current_state.get("messages"):
            last_message = self.current_state["messages"][-1]
            if hasattr(last_message, 'content'):
                try:
                    # Try to parse as JSON - if successful, it's a UI message
                    ui_message = json.loads(last_message.content)
                    if isinstance(ui_message, dict) and ui_message.get("sender") == "bot":
                        # This is a UI message, return it as-is for the frontend to handle
                        return last_message.content
                except (json.JSONDecodeError, AttributeError):
                    pass  # Not a JSON message, continue with text processing
        
        # Fallback to text-based response generation
        response_parts = []
        
        # Check for validation errors
        if self.current_state.get("last_error"):
            response_parts.append(f"❌ {self.current_state['last_error']}")
            response_parts.append("Please try again:")
        
        # Get the current question
        question = self._get_current_question()
        if question:
            response_parts.append(question)
        
        # Show enhanced progress tracking
        if self.workflow:
            progress_info = self._calculate_progress()
            response_parts.append(f"\n*{progress_info}*")
        
        return "\n\n".join(response_parts) if response_parts else None
    
    def _calculate_progress(self) -> str:
        """Calculate and format progress information more accurately."""
        if not self.current_state or not self.workflow:
            return "Progress: Starting..."
        
        total_main_questions = len(self.workflow.questions)
        completed_main_questions = len(self.current_state.get("questions_completed", []))
        current_question_index = self.current_state.get("current_question_index", 0)
        
        # For basic progress, we use the number of main questions completed
        # This provides a consistent reference point regardless of retries or sub-questions
        
        # Check if we're in a complex question type
        if self.current_state.get("current_repeat_group_question"):
            # In a repeat group (like vehicle details)
            repeat_group = self.current_state["current_repeat_group_question"]
            instance_index = self.current_state.get("current_repeat_instance", 0)
            field_index = self.current_state.get("current_repeat_field_index", 0)
            total_fields = len(repeat_group["fields"])
            
            # Calculate progress within this question group
            sub_progress = f" - Vehicle {instance_index + 1}, detail {field_index + 1}/{total_fields}"
            return f"Progress: Question {completed_main_questions + 1}/{total_main_questions}{sub_progress}"
            
        elif self.current_state.get("current_group_question"):
            # In a group question (multiple parts)
            group_question = self.current_state["current_group_question"]
            field_index = self.current_state.get("current_group_field_index", 0)
            total_fields = len(group_question["fields"])
            
            # Calculate progress within this question group
            sub_progress = f" - Part {field_index + 1}/{total_fields}"
            return f"Progress: Question {completed_main_questions + 1}/{total_main_questions}{sub_progress}"
            
        else:
            # Regular question or initial question setup
            # Use completed questions + 1 for current question (unless we're retrying)
            current_display = completed_main_questions + 1
            
            # If we're on a question that's already completed, it means we're retrying
            current_question_id = self.current_state.get("current_question_id")
            if current_question_id in self.current_state.get("questions_completed", []):
                return f"Progress: Question {completed_main_questions}/{total_main_questions} - Clarifying your answer"
            
            return f"Progress: Question {current_display}/{total_main_questions}"
    
    def _generate_completion_message(self) -> str:
        """Generate completion message with form summary."""
        if not self.current_state or not self.workflow:
            return "🎉 **Form completed!** Thank you for providing the information."
        
        form_data = self.current_state.get("form_data", {})
        
        message_parts = [
            "🎉 **Accident Report Completed Successfully!**",
            "",
            "📋 **Summary of Information Collected:**"
        ]
        
        for question_id, answer in form_data.items():
            question = self.workflow.get_question_by_id(question_id)
            if question:
                question_text = question["question"]
                
                if isinstance(answer, dict):
                    answer_text = ", ".join([f"{k}: {v}" for k, v in answer.items()])
                elif isinstance(answer, list):
                    answer_text = ", ".join(str(item) for item in answer)
                else:
                    answer_text = str(answer)
                
                message_parts.append(f"• **{question_text}**: {answer_text}")
        
        message_parts.extend([
            "",
            "The accident report has been completed. You can now continue chatting with the wizard if needed.",
            "",
            "💾 *Note: The form data has been saved for your records.*"
        ])
        
        return "\n".join(message_parts)


class WebAIBotSession:
    """AI-powered bot session that handles ambiguous inputs and smart clarifications."""
    
    def __init__(self, room_id: str, questions_file: str = None):
        self.room_id = room_id
        self.is_active = False
        
        # Default questions file path
        if questions_file is None:
            questions_file = ACCIDENT_REPORT_DIR / "questionnaire" / "questions.json"
        
        self.questions_file = str(questions_file)
        
        # Initialize the AI workflow if possible
        if AI_BOT_IMPORTS_SUCCESSFUL and AIBotWorkflow and os.path.exists(self.questions_file):
            try:
                self.workflow = AIBotWorkflow(self.questions_file, interactive=False)
                self.graph = self.workflow.compile_graph()
                self.config = {"configurable": {"thread_id": f"ai_session_{room_id}"}, "recursion_limit": 100}
                self.current_state = None
                print(f"✅ AI Bot initialized for room {room_id}")
            except Exception as e:
                print(f"❌ Failed to initialize AI bot for room {room_id}: {e}")
                self.workflow = None
                self.graph = None
        else:
            self.workflow = None
            self.graph = None
            if not AI_BOT_IMPORTS_SUCCESSFUL:
                print(f"⚠️ AI Bot not available for room {room_id} (import failed)")
            elif not os.path.exists(self.questions_file):
                print(f"⚠️ AI Bot not available for room {room_id} (questions file not found)")
            else:
                print(f"⚠️ AI Bot not available for room {room_id} (missing dependencies)")
    
    def start(self) -> Optional[str]:
        """Start the AI bot session and return the initial message."""
        if not self.workflow or not self.graph:
            return "❌ AI Bot is not available. Please check the configuration."
        
        try:
            self.is_active = True
            # Run until first "ask" step
            for _ in self.graph.stream({}, config=self.config):
                pass
            
            # Get the current state after asking the first question
            state = self.graph.get_state(self.config).values
            self.current_state = state
            
            question = state.get("rephrased_question", "Let's begin with your accident report...")
            return f"🤖 **AI Accident Report Bot Activated**\n\n{question}"
            
        except Exception as e:
            print(f"❌ Error starting AI bot session: {e}")
            import traceback
            traceback.print_exc()
            self.is_active = False
            return f"❌ Failed to start AI bot: {str(e)}"
    
    def process_message(self, user_message: str) -> Optional[str]:
        """Process a user message and return the bot's response."""
        if not self.is_active or not self.workflow or not self.graph:
            return None
        
        try:
            # Get current state and add user message
            state = self.graph.get_state(self.config).values
            updated_state = {
                **state, 
                "messages": state.get("messages", []) + [HumanMessage(content=user_message)]
            }
            
            # Update state and run interpret + validate
            self.graph.update_state(self.config, updated_state)
            for _ in self.graph.stream(None, config=self.config, stream_mode="values"):
                pass
            
            # Get new state
            new_state = self.graph.get_state(self.config).values
            self.current_state = new_state
            
            if new_state.get("done"):
                self.is_active = False
                return "🎉 **Form completed!** Thanks for providing all the accident details. Your data has been saved."
            
            # Return either a clarifier or the next question
            clarifier = new_state.get("clarifying_question")
            if clarifier:
                return f"🔎 {clarifier}"
            
            question = new_state.get("rephrased_question")
            if question:
                return f"❓ {question}"
            
            return "Please continue..."
            
        except Exception as e:
            print(f"❌ Error processing message in AI bot: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error: {str(e)}. Please try again or restart the bot."
    
    def stop(self) -> str:
        """Stop the AI bot session."""
        self.is_active = False
        return "🤖 **AI Bot Deactivated**\n\nThe AI accident report bot has been stopped. You can now chat normally."
    
    def get_status(self) -> Dict[str, Any]:
        """Get current AI bot session status."""
        if not self.current_state:
            return {
                "active": self.is_active,
                "available": self.workflow is not None,
                "progress": "Not started",
                "bot_type": "ai"
            }
        
        total_questions = len(self.workflow.questions) if self.workflow else 0
        completed_questions = len(self.current_state.get("questions_completed", []))
        
        return {
            "active": self.is_active,
            "available": self.workflow is not None,
            "progress": f"{completed_questions}/{total_questions} questions completed",
            "form_complete": self.current_state.get("done", False),
            "bot_type": "ai"
        }


class BotManager:
    """Manages bot sessions for multiple rooms."""
    
    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self.session_type: Dict[str, str] = {}
    
    def start_bot(self, room_id: str, bot_type: str = "rule") -> Optional[str]:
        """Start a bot session for a room."""
        # Reuse existing if same type & active
        if room_id in self.sessions and self.session_type.get(room_id) == bot_type:
            if self.sessions[room_id].is_active:
                return f"🤖 {bot_type.title()} Bot is already active in this room."
            else:
                # Restart existing session
                return self.sessions[room_id].start()
        
        # Create new session based on type
        if bot_type == "ai":
            if not AI_BOT_IMPORTS_SUCCESSFUL:
                return "❌ AI Bot is not available. Missing dependencies or configuration."
            session = WebAIBotSession(room_id)
        else:
            if not BOT_IMPORTS_SUCCESSFUL:
                return "❌ Rule-based Bot is not available. Missing dependencies or configuration."
            session = WebBotSession(room_id)
        
        self.sessions[room_id] = session
        self.session_type[room_id] = bot_type
        return session.start()
    
    def stop_bot(self, room_id: str) -> str:
        """Stop a bot session for a room."""
        if room_id in self.sessions:
            response = self.sessions[room_id].stop()
            # Keep the session for potential restart
            return response
        return "🤖 No active bot session found."
    
    def process_message(self, room_id: str, message: str) -> Optional[str]:
        """Process a message through the bot if active."""
        if room_id in self.sessions and self.sessions[room_id].is_active:
            return self.sessions[room_id].process_message(message)
        return None
    
    def get_bot_status(self, room_id: str) -> Dict[str, Any]:
        """Get bot status for a room."""
        if room_id in self.sessions:
            status = self.sessions[room_id].get_status()
            status["bot_type"] = self.session_type.get(room_id, "unknown")
            return status
        
        # Check if bots are available
        questions_file = ACCIDENT_REPORT_DIR / "questionnaire" / "questions.json"
        rule_available = BOT_IMPORTS_SUCCESSFUL and FormWorkflow is not None and questions_file.exists()
        ai_available = AI_BOT_IMPORTS_SUCCESSFUL and AIBotWorkflow is not None and questions_file.exists()
        
        return {
            "active": False,
            "available": rule_available or ai_available,
            "rule_bot_available": rule_available,
            "ai_bot_available": ai_available,
            "progress": "Not started",
            "bot_type": None
        }
    
    def is_bot_active(self, room_id: str) -> bool:
        """Check if bot is active in a room."""
        return (room_id in self.sessions and 
                self.sessions[room_id].is_active)
    
    def get_available_bot_types(self) -> Dict[str, bool]:
        """Get available bot types."""
        questions_file = ACCIDENT_REPORT_DIR / "questionnaire" / "questions.json"
        
        return {
            "rule": BOT_IMPORTS_SUCCESSFUL and FormWorkflow is not None and questions_file.exists(),
            "ai": AI_BOT_IMPORTS_SUCCESSFUL and AIBotWorkflow is not None and questions_file.exists()
        }


# Global bot manager instance
bot_manager = BotManager()
