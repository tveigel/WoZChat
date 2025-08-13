"""
Navigation Impact Analyzer for Rule-Based Bot

This module analyzes the impact of editing previous answers and determines
the appropriate navigation strategy based on question types and dependencies.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import json


class NavigationImpactAnalyzer:
    """Analyzes the impact of editing previous answers on the conversation flow."""
    
    def __init__(self, questions_data: Dict[str, Any]):
        """Initialize with the questions data structure."""
        self.questions_data = questions_data
        self.questions = questions_data.get("questions", [])
        self._build_dependency_map()
    
    def _build_dependency_map(self):
        """Build a map of question dependencies and impacts."""
        self.branching_questions = set()
        self.repeat_group_triggers = set()
        self.question_dependencies = {}
        
        for question in self.questions:
            q_id = question["id"]
            
            # Identify branching questions (have followup_if_yes)
            if question.get("followup_if_yes"):
                self.branching_questions.add(q_id)
                followup_id = question["followup_if_yes"]["id"]
                self.question_dependencies[followup_id] = q_id
            
            # Identify repeat group triggers
            if question["type"] == "repeat_group":
                self.repeat_group_triggers.add(q_id)
            
            # Check for questions that might affect repeat group counts
            if "number" in q_id.lower() and ("vehicle" in q_id.lower() or "participant" in q_id.lower()):
                # This is likely a question that affects how many instances we need
                for other_q in self.questions:
                    if other_q["type"] == "repeat_group":
                        self.question_dependencies[other_q["id"]] = q_id
    
    def analyze_edit_impact(self, edited_question_id: str, new_value: Any, 
                          current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the impact of editing a specific question.
        
        Args:
            edited_question_id: ID of the question being edited
            new_value: The new value for the question
            current_state: Current conversation state
            
        Returns:
            Dict containing navigation strategy and impact analysis
        """
        result = {
            "strategy": "continue",  # continue, restart_branch, restart_from_edit, confirm_and_restart
            "reason": "",
            "affected_questions": [],
            "requires_confirmation": False,
            "confirmation_message": "",
            "restart_from_question_id": None,
            "data_to_clear": []
        }
        
        # Get the edited question definition
        edited_question = self._get_question_by_id(edited_question_id)
        if not edited_question:
            result["strategy"] = "continue"
            result["reason"] = "Question not found, continuing normally"
            return result
        
        # Check if this is a branching question
        if edited_question_id in self.branching_questions:
            return self._analyze_branching_question_edit(
                edited_question_id, new_value, current_state, result
            )
        
        # Check if this affects repeat group counts
        if self._affects_repeat_group_count(edited_question_id, new_value, current_state):
            return self._analyze_repeat_group_count_edit(
                edited_question_id, new_value, current_state, result
            )
        
        # Check if this is editing within a repeat group
        if self._is_repeat_group_field_edit(edited_question_id, current_state):
            return self._analyze_repeat_group_field_edit(
                edited_question_id, new_value, current_state, result
            )
        
        # Default: simple question edit
        result["strategy"] = "continue"
        result["reason"] = f"Simple question edit for '{edited_question_id}' - no dependencies affected"
        return result
    
    def _analyze_branching_question_edit(self, question_id: str, new_value: Any, 
                                       current_state: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze edit impact for branching questions."""
        old_value = current_state.get("form_data", {}).get(question_id)
        
        # Convert values to boolean for comparison
        old_bool = self._to_boolean(old_value)
        new_bool = self._to_boolean(new_value)
        
        if old_bool == new_bool:
            # Same branch, just update and continue
            result["strategy"] = "continue"
            result["reason"] = f"Branch unchanged for '{question_id}' - continuing from current position"
            return result
        
        # Branch changed - need to restart from this question
        question_def = self._get_question_by_id(question_id)
        followup_id = question_def.get("followup_if_yes", {}).get("id")
        
        if new_bool and followup_id:
            # Changed to Yes - will now have followup
            result["strategy"] = "restart_branch"
            result["reason"] = f"Changed to 'Yes' for '{question_id}' - will show followup question"
            result["restart_from_question_id"] = question_id
            result["affected_questions"] = [followup_id]
        elif not new_bool and followup_id:
            # Changed to No - need to clear followup data
            result["strategy"] = "restart_branch"
            result["reason"] = f"Changed to 'No' for '{question_id}' - removing followup question"
            result["restart_from_question_id"] = question_id
            result["affected_questions"] = [followup_id]
            result["data_to_clear"] = [followup_id]
        
        return result
    
    def _analyze_repeat_group_count_edit(self, question_id: str, new_value: Any, 
                                       current_state: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze edit impact when changing repeat group counts."""
        old_count = self._extract_count_from_value(current_state.get("form_data", {}).get(question_id))
        new_count = self._extract_count_from_value(new_value)
        
        if old_count == new_count:
            result["strategy"] = "continue"
            result["reason"] = f"Count unchanged for '{question_id}' - continuing from current position"
            return result
        
        # Find affected repeat groups
        affected_repeat_groups = []
        for q in self.questions:
            if q["type"] == "repeat_group" and self.question_dependencies.get(q["id"]) == question_id:
                affected_repeat_groups.append(q["id"])
        
        if not affected_repeat_groups:
            result["strategy"] = "continue"
            result["reason"] = f"No repeat groups affected by '{question_id}' edit"
            return result
        
        if new_count > old_count:
            # Adding items - can continue and ask for new items
            result["strategy"] = "continue"
            result["reason"] = f"Increased count from {old_count} to {new_count} - will collect additional data"
            result["affected_questions"] = affected_repeat_groups
        elif new_count < old_count:
            # Removing items - need confirmation
            result["strategy"] = "confirm_and_restart"
            result["reason"] = f"Decreased count from {old_count} to {new_count} - some data will be lost"
            result["requires_confirmation"] = True
            result["confirmation_message"] = (
                f"You've changed the number from {old_count} to {new_count}. "
                f"This will remove data for {old_count - new_count} items. "
                f"Are you sure you want to continue? (Type 'yes' to confirm or 'no' to cancel)"
            )
            result["affected_questions"] = affected_repeat_groups
            result["restart_from_question_id"] = question_id
        
        return result
    
    def _analyze_repeat_group_field_edit(self, question_id: str, new_value: Any, 
                                       current_state: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze edit impact for fields within repeat groups."""
        # For now, editing individual repeat group fields is safe - just update and continue
        result["strategy"] = "continue"
        result["reason"] = f"Updated field '{question_id}' within repeat group - no dependencies affected"
        return result
    
    def _affects_repeat_group_count(self, question_id: str, new_value: Any, current_state: Dict[str, Any]) -> bool:
        """Check if editing this question affects repeat group counts."""
        # Check if any repeat groups depend on this question
        for q in self.questions:
            if q["type"] == "repeat_group" and self.question_dependencies.get(q["id"]) == question_id:
                return True
        
        # Also check based on question content
        if "number" in question_id.lower() and ("vehicle" in question_id.lower() or "participant" in question_id.lower()):
            return True
            
        return False
    
    def _is_repeat_group_field_edit(self, question_id: str, current_state: Dict[str, Any]) -> bool:
        """Check if this is editing a field within a repeat group."""
        # Look through all repeat groups to see if this question_id is a field
        for question in self.questions:
            if question["type"] == "repeat_group":
                for field in question.get("fields", []):
                    if field["id"] == question_id:
                        return True
        return False
    
    def _get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get question definition by ID."""
        for question in self.questions:
            if question["id"] == question_id:
                return question
            # Also check within repeat groups and groups
            if question["type"] in ["repeat_group", "group"]:
                for field in question.get("fields", []):
                    if field["id"] == question_id:
                        return field
            # Check followup questions
            if question.get("followup_if_yes", {}).get("id") == question_id:
                return question["followup_if_yes"]
        return None
    
    def _to_boolean(self, value: Any) -> bool:
        """Convert various value types to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['yes', 'true', '1', 'y']
        if isinstance(value, (int, float)):
            return bool(value)
        return False
    
    def _extract_count_from_value(self, value: Any) -> int:
        """Extract count from various value formats."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            # Try to extract number from strings like "2", "Two", "2 vehicles"
            import re
            numbers = re.findall(r'\d+', str(value))
            if numbers:
                return int(numbers[0])
            # Handle word numbers
            word_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }
            for word, num in word_to_num.items():
                if word in str(value).lower():
                    return num
        return 0


def get_navigation_strategy(questions_data: Dict[str, Any], edited_question_id: str, 
                          new_value: Any, current_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to get navigation strategy for a question edit.
    
    Args:
        questions_data: The questions configuration
        edited_question_id: ID of the edited question
        new_value: New value for the question
        current_state: Current conversation state
        
    Returns:
        Navigation strategy dictionary
    """
    analyzer = NavigationImpactAnalyzer(questions_data)
    return analyzer.analyze_edit_impact(edited_question_id, new_value, current_state)


# Export main classes and functions
__all__ = [
    'NavigationImpactAnalyzer',
    'get_navigation_strategy'
]
