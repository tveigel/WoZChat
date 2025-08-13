"""
UI Components Module for Rule-Based Bot

This module provides clickable UI components for form questions, allowing participants
to interact with forms through clickable buttons in addition to text input.

Features:
- Clickable single choice questions
- Clickable multiple choice questions  
- Fallback to text input for unsupported question types
- Support for 'other' option specification
- Compatible with web interface via JSON message format
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import json


class UIComponent:
    """Base class for UI components."""
    
    def __init__(self, component_type: str, question_id: str, question_text: str):
        self.type = component_type
        self.question_id = question_id
        self.question_text = question_text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "question_id": self.question_id,
            "question_text": self.question_text
        }


class ClickableChoiceComponent(UIComponent):
    """Clickable component for single and multiple choice questions."""
    
    def __init__(self, question_id: str, question_text: str, options: List[str], 
                 allow_multiple: bool = False, allow_other: bool = False):
        component_type = "clickable_choice"
        super().__init__(component_type, question_id, question_text)
        self.options = options
        self.allow_multiple = allow_multiple
        self.allow_other = allow_other
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            "options": self.options,
            "allow_multiple": self.allow_multiple,
            "allow_other": self.allow_other,
            "instructions": self._get_instructions()
        })
        return base_dict
    
    def _get_instructions(self) -> str:
        """Generate user instructions for the component."""
        if self.allow_multiple:
            base = "Click one or more options below:"
            if self.allow_other:
                base += " (Select 'Other' and specify if needed)"
        else:
            base = "Click one option below:"
            if self.allow_other:
                base += " (Select 'Other' and specify if needed)"
        return base


class TextInputComponent(UIComponent):
    """Standard text input component for questions that don't support clicking."""
    
    def __init__(self, question_id: str, question_text: str, input_type: str = "text",
                 placeholder: str = "", hint: str = ""):
        component_type = "text_input"
        super().__init__(component_type, question_id, question_text)
        self.input_type = input_type  # text, number, date, time, etc.
        self.placeholder = placeholder
        self.hint = hint
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            "input_type": self.input_type,
            "placeholder": self.placeholder,
            "hint": self.hint
        })
        return base_dict


class UIComponentFactory:
    """Factory class for creating appropriate UI components based on question definitions."""
    
    @staticmethod
    def create_component(question_def: Dict[str, Any], 
                        current_field: Optional[Dict[str, Any]] = None) -> UIComponent:
        """
        Create appropriate UI component based on question definition.
        
        Args:
            question_def: Question definition from questions.json
            current_field: For group/repeat_group questions, the current field being asked
            
        Returns:
            UIComponent: Appropriate component for the question type
        """
        # Use current_field if provided (for group/repeat_group sub-questions)
        field_def = current_field if current_field else question_def
        
        question_id = field_def.get("id", "unknown")
        question_text = field_def.get("question", "")
        question_type = field_def.get("type", "text")
        
        # Create clickable components for choice questions
        if question_type in ["single_choice", "multiple_choice"]:
            options = field_def.get("options", [])
            allow_multiple = question_type == "multiple_choice"
            allow_other = field_def.get("other_specify", False)
            
            return ClickableChoiceComponent(
                question_id=question_id,
                question_text=question_text,
                options=options,
                allow_multiple=allow_multiple,
                allow_other=allow_other
            )
        
        # Create text input components for other question types
        else:
            input_type, placeholder, hint = UIComponentFactory._get_text_input_config(field_def)
            
            return TextInputComponent(
                question_id=question_id,
                question_text=question_text,
                input_type=input_type,
                placeholder=placeholder,
                hint=hint
            )
    
    @staticmethod
    def _get_text_input_config(field_def: Dict[str, Any]) -> tuple:
        """Get configuration for text input components based on question type."""
        question_type = field_def.get("type", "text")
        question_text = field_def.get("question", "").lower()
        
        # Configure based on question type
        if question_type == "number":
            if "speed" in question_text:
                return "number", "e.g., 30", "Enter speed in km/h"
            else:
                return "number", "Enter a number", "Please enter a numeric value"
                
        elif question_type == "date":
            return "date", "YYYY-MM-DD", "Select or enter date in YYYY-MM-DD format"
            
        elif question_type == "time":
            return "time", "HH:MM", "Select or enter time in HH:MM format"
            
        elif question_type == "boolean":
            return "text", "yes/no", "Type 'yes' or 'no'"
            
        elif question_type in ["text", "multiline_text"]:
            # Provide context-specific placeholders
            if "licence" in question_text or "license" in question_text:
                return "text", "e.g., ABC-1234", "Enter the license plate number"
            elif "make" in question_text and "model" in question_text:
                return "text", "e.g., Toyota Camry", "Enter vehicle make and model"
            elif "damage" in question_text:
                return "text", "e.g., Front bumper dented", "Describe the damage"
            elif "description" in question_text:
                return "textarea", "Provide details...", "Enter a detailed description"
            else:
                input_type = "textarea" if question_type == "multiline_text" else "text"
                return input_type, "Enter your answer...", "Please provide your response"
        
        # Default configuration
        return "text", "Enter your answer...", "Please provide your response"


class UIMessageFormatter:
    """Formats bot messages with UI components for web interface."""
    
    @staticmethod
    def create_ui_message(text_content: str, ui_component: Optional[Union[UIComponent, Dict[str, Any]]] = None,
                         show_progress: bool = True, progress_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a formatted message with optional UI component for web interface.
        
        Args:
            text_content: The text content of the message
            ui_component: Optional UI component to include (UIComponent object or dict)
            show_progress: Whether to show progress information
            progress_info: Progress information (current/total questions)
            
        Returns:
            Dict containing formatted message for web interface
        """
        message = {
            "sender": "bot",
            "text": text_content,
            "timestamp": None  # Will be set by the calling code
        }
        
        # Add UI component if provided
        if ui_component:
            if isinstance(ui_component, dict):
                message["ui_component"] = ui_component
            else:
                message["ui_component"] = ui_component.to_dict()
            
        # Add progress information if provided
        if show_progress and progress_info:
            message["progress"] = progress_info
            
        return message
    
    @staticmethod
    def format_choice_question_text(question_text: str, options: List[str], 
                                  allow_other: bool = False, allow_multiple: bool = False) -> str:
        """
        Format the text content for choice questions.
        
        Args:
            question_text: The main question text
            options: List of available options
            allow_other: Whether "other" option is allowed
            allow_multiple: Whether multiple selections are allowed
            
        Returns:
            Formatted text content
        """
        formatted_text = f"❓ {question_text}\n\n"
        
        if allow_multiple:
            formatted_text += "You can click one or more options below, or type your answer:\n\n"
        else:
            formatted_text += "You can click one option below, or type your answer:\n\n"
            
        # Add text options for reference (in case JavaScript is disabled)
        formatted_text += "Options:\n"
        for i, option in enumerate(options, 1):
            formatted_text += f"  {i}. {option}\n"
            
        if allow_other:
            formatted_text += "\n💡 You can also specify 'Other' with custom details"
            
        return formatted_text
    
    @staticmethod
    def format_text_question_text(question_text: str, question_type: str, 
                                hint: str = "") -> str:
        """
        Format the text content for text input questions.
        
        Args:
            question_text: The main question text
            question_type: Type of question (text, number, date, etc.)
            hint: Additional hint for the user
            
        Returns:
            Formatted text content
        """
        formatted_text = f"❓ {question_text}\n\n"
        
        if hint:
            formatted_text += f"💡 {hint}\n\n"
            
        formatted_text += "Please type your answer below:"
        
        return formatted_text


def create_ui_message_for_question(question_def: Dict[str, Any], 
                                 current_field: Optional[Dict[str, Any]] = None,
                                 progress_info: Optional[Dict[str, Any]] = None,
                                 retry_info: Optional[Dict[str, Any]] = None,
                                 completed_questions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convenience function to create a complete UI message for a question.
    
    Args:
        question_def: Question definition from questions.json
        current_field: For group/repeat_group questions, the current field
        progress_info: Progress information (current/total)
        retry_info: Retry information if validation failed
        completed_questions: List of completed question IDs for navigation context
        
    Returns:
        Complete message dictionary ready for web interface
    """
    # Use current_field if provided (for group/repeat_group sub-questions)
    field_def = current_field if current_field else question_def
    
    # Create UI component
    ui_component = UIComponentFactory.create_component(question_def, current_field)
    
    # Add navigation context to UI component
    ui_component_dict = ui_component.to_dict()
    ui_component_dict["is_current_question"] = True
    ui_component_dict["enabled"] = True  # Only current questions are enabled for clicking
    
    # Disable previous questions to prevent clickable navigation
    # Users should use "change reply" command instead
    if completed_questions:
        ui_component_dict["completed_questions"] = [
            {
                "question_id": q_id,
                "enabled": False  # Previous questions not clickable
            }
            for q_id in completed_questions
        ]
    
    # Format text content based on component type
    if isinstance(ui_component, ClickableChoiceComponent):
        text_content = UIMessageFormatter.format_choice_question_text(
            field_def.get("question", ""),
            field_def.get("options", []),
            field_def.get("other_specify", False),
            field_def.get("type") == "multiple_choice"
        )
    else:
        text_content = UIMessageFormatter.format_text_question_text(
            field_def.get("question", ""),
            field_def.get("type", "text"),
            ui_component.hint if hasattr(ui_component, 'hint') else ""
        )
    
    # Add retry error message if provided
    if retry_info and retry_info.get("error"):
        text_content = f"❌ {retry_info['error']}\nLet me ask that again...\n\n{text_content}"
    
    # Add progress information to text if available
    if progress_info:
        current = progress_info.get("current", 0)
        total = progress_info.get("total", 0)
        if current > 0 and total > 0:
            progress_text = f"📋 Question {current}/{total}\n" + "-" * 40 + "\n\n"
            text_content = progress_text + text_content
    
    # Create complete message
    return UIMessageFormatter.create_ui_message(
        text_content=text_content,
        ui_component=ui_component_dict,  # Use the enhanced dict instead of the object
        show_progress=bool(progress_info),
        progress_info=progress_info
    )


def parse_ui_response(user_input: str, ui_component_data: Optional[Dict[str, Any]] = None) -> Tuple[str, Optional[str]]:
    """
    Parse user response from UI interactions or text input.
    
    This function handles responses from clickable UI components and converts them
    back to the format expected by the validator.
    
    Args:
        user_input: Raw user input (could be text or UI interaction data)
        ui_component_data: Data about the UI component that was shown
        
    Returns:
        Tuple of (processed_user_input, edited_question_id)
        edited_question_id is always None since navigation edits are disabled
    """
    # If input looks like a UI component response (JSON), parse it
    if user_input.strip().startswith("{") and user_input.strip().endswith("}"):
        try:
            ui_response = json.loads(user_input)
            
            # Handle clickable choice responses (navigation edits are disabled)
            if ui_response.get("type") == "choice_selection":
                selected_options = ui_response.get("selected_options", [])
                other_text = ui_response.get("other_text", "")
                
                if len(selected_options) == 1 and not other_text:
                    # Single selection
                    return selected_options[0], None
                elif len(selected_options) == 1 and selected_options[0].lower() == "other" and other_text:
                    # Other option with specification
                    return f"Other: {other_text}", None
                elif len(selected_options) > 1:
                    # Multiple selections
                    return ", ".join(selected_options), None
                else:
                    # Fallback to raw input
                    return user_input, None
                    
        except json.JSONDecodeError:
            pass  # Not JSON, treat as regular text input
    
    # Return as-is for regular text input
    return user_input, None


# Export main functions for easy importing
__all__ = [
    'UIComponent',
    'ClickableChoiceComponent', 
    'TextInputComponent',
    'UIComponentFactory',
    'UIMessageFormatter',
    'create_ui_message_for_question',
    'parse_ui_response'
]
