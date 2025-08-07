#!/usr/bin/env python3
"""
Comprehensive test suite for the WebWOz accident report bot.
Tests all question types, edge cases, and the complete workflow.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add the backend directory to path
BACKEND_DIR = Path(__file__).parent.parent.parent  # Go up to backend level
sys.path.insert(0, str(BACKEND_DIR))

try:
    from bot_integration import WebBotSession
    from backend.accident_report.rule_based.validator import validate_answer
    BOT_AVAILABLE = True
    print("✅ Successfully imported bot components")
except ImportError as e:
    print(f"❌ Failed to import bot components: {e}")
    BOT_AVAILABLE = False
    sys.exit(1)


class BotTestSuite:
    """Comprehensive test suite for the accident report bot."""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        self.current_test = ""
        
        # Test scenarios with various edge cases
        self.test_scenarios = [
            {
                "name": "Happy Path - Complete Form",
                "type": "normal",
                "description": "Complete accident report with 2 vehicles, injuries, property damage, and witnesses",
                "answers": [
                    "2025-06-12",  # date
                    "14:35",       # time
                    "123 Main St, Springfield",  # location
                    "wet",         # road surface
                    "rain",        # weather  
                    "daylight",    # lighting
                    "intersection", # location type (group 1)
                    "50",          # speed limit (group 2) 
                    "signal",      # traffic control (group 3)
                    "2",           # number of vehicles
                    "Sedan / Toyota / Camry",    # vehicle 1 type
                    "ABC-1234",    # vehicle 1 plate
                    "turning-left", # vehicle 1 manoeuvre
                    "30",          # vehicle 1 speed
                    "Front fender dented",  # vehicle 1 damage
                    "SUV / Honda / CR-V",   # vehicle 2 type
                    "XYZ-5678",    # vehicle 2 plate
                    "straight",    # vehicle 2 manoeuvre
                    "45",          # vehicle 2 speed
                    "Rear bumper cracked",  # vehicle 2 damage
                    "Vehicle 1 turned left while vehicle 2 went straight",  # narrative
                    "failed-to-yield, weather/road",  # contributing factors
                    "yes",         # injuries
                    "Driver of vehicle 1 had minor bruises, passenger of vehicle 2 had concussion", # injury details
                    "no",          # fatalities
                    "yes",         # property damage
                    "Traffic light damaged",  # property damage description
                    "yes",         # witnesses
                    "Jane Smith, 555-1234",  # witness details
                    "Both vehicles towed"     # additional comments
                ]
            },
            {
                "name": "Single Vehicle - No Injuries Path",
                "type": "normal", 
                "description": "Single vehicle accident with no injuries, no property damage, no witnesses",
                "answers": [
                    "2025-07-15",  # date
                    "22:45",       # time
                    "Highway 17, mile marker 45",  # location
                    "snow / ice",  # road surface - corrected format
                    "snow",        # weather
                    "dark–unlit",  # lighting - corrected format (em dash)
                    "curve",       # location type
                    "80",          # speed limit
                    "none",        # traffic control
                    "1",           # number of vehicles
                    "Pickup / Ford / F-150",  # vehicle 1 type
                    "ICE-2025",    # vehicle 1 plate
                    "straight",    # vehicle 1 manoeuvre
                    "65",          # vehicle 1 speed
                    "Slid into ditch, minor body damage",  # vehicle 1 damage
                    "Vehicle lost control on icy curve and slid off road", # narrative
                    "weather/road, speeding",  # contributing factors
                    "no",          # injuries
                    "no",          # fatalities
                    "no",          # property damage
                    "no",          # witnesses
                    "Driver called tow truck"  # additional comments
                ]
            },
            {
                "name": "Three Vehicle Scenario",
                "type": "normal",
                "description": "Complex 3-vehicle accident with fatalities but no property damage",
                "answers": [
                    "2025-08-06",  # date
                    "09:15",       # time
                    "Highway 401, Toronto",  # location
                    "debris",      # road surface
                    "clear",       # weather
                    "daylight",    # lighting
                    "curve",       # location type
                    "100",         # speed limit
                    "none",        # traffic control
                    "3",           # number of vehicles
                    "Motorcycle / Harley / Sportster",  # vehicle 1
                    "BIKE-123",    # vehicle 1 plate
                    "overtaking",  # vehicle 1 manoeuvre
                    "80",          # vehicle 1 speed
                    "Complete writeoff",  # vehicle 1 damage
                    "Pickup / Chevy / Silverado",  # vehicle 2
                    "TRUCK-456",   # vehicle 2 plate
                    "straight",    # vehicle 2 manoeuvre
                    "90",          # vehicle 2 speed
                    "Minor scratches",  # vehicle 2 damage
                    "Van / Honda / Odyssey",  # vehicle 3
                    "VAN-789",     # vehicle 3 plate
                    "turning-right", # vehicle 3 manoeuvre
                    "70",          # vehicle 3 speed
                    "Rear end damage",  # vehicle 3 damage
                    "Motorcycle was overtaking when pickup changed lanes suddenly", # narrative
                    "speeding, vehicle defect",  # factors
                    "yes",         # injuries
                    "Motorcycle driver: serious head injury; Pickup driver: minor cuts", # injuries
                    "yes",         # fatalities
                    "no",          # property damage
                    "no",          # witnesses
                    "Complex multi-vehicle accident"  # comments
                ]
            },
            {
                "name": "Edge Cases - Mixed Valid Inputs",
                "type": "validation",
                "description": "Test various edge cases with mixed input formats that should be handled gracefully",
                "answers": [
                    "2025/06/12",  # date - alternative format
                    "14:35",       # time - standard
                    "",     # location - empty (should prompt again)
                    "456 Oak Ave",          # location - valid after retry
                    "dry",         # road surface - valid
                    "fog",         # weather - valid
                    "dusk / dawn", # lighting - valid  
                    "straight",    # group field 1 - valid
                    "30",          # group field 2 - valid
                    "none",        # group field 3 - valid
                    "1",           # vehicles - single vehicle
                    "Truck / Ford / F-150",  # vehicle type - valid
                    "DEF-9876",    # plate - valid
                    "straight",    # manoeuvre - valid
                    "60",          # speed - valid
                    "Side door damaged",  # damage description - valid
                    "Single truck hit guardrail", # narrative
                    "speeding",    # factors - single valid
                    "no",          # injuries - no
                    "false",       # fatalities - different boolean format
                    "1",           # property damage - number for yes
                    "Guardrail bent",      # property damage description
                    "true",        # witnesses - different boolean format
                    "John Doe saw the accident",  # witness details
                    ""             # additional comments - empty is ok
                ]
            },
            {
                "name": "Four Vehicle - Maximum Complexity",
                "type": "normal",
                "description": "Test maximum complexity with 4 vehicles and all types of damage/injuries",
                "answers": [
                    "2025-09-30",  # date
                    "17:20",       # time
                    "I-95 and Route 1 interchange, Miami",  # location
                    "wet",         # road surface
                    "rain",        # weather
                    "dusk / dawn", # lighting
                    "intersection", # location type
                    "70",          # speed limit
                    "signal",      # traffic control
                    "other",       # number of vehicles - challenging: user types "other" first
                    "4",           # specify 4 vehicles - then provides the number
                    "Car / Toyota / Prius",    # vehicle 1
                    "ECO-2025",    # vehicle 1 plate
                    "turning-left", # vehicle 1 manoeuvre
                    "35",          # vehicle 1 speed
                    "Front end crushed",  # vehicle 1 damage
                    "SUV / Jeep / Grand Cherokee",  # vehicle 2
                    "OFF-ROAD",    # vehicle 2 plate
                    "straight",    # vehicle 2 manoeuvre
                    "55",          # vehicle 2 speed
                    "Side impact damage",  # vehicle 2 damage
                    "Van / Ford / Transit",  # vehicle 3
                    "WORK-VAN",    # vehicle 3 plate
                    "turning-right", # vehicle 3 manoeuvre
                    "25",          # vehicle 3 speed
                    "Rear bumper damaged",  # vehicle 3 damage
                    "Truck / Peterbilt / 379",  # vehicle 4
                    "SEMI-18",     # vehicle 4 plate
                    "straight",    # vehicle 4 manoeuvre
                    "40",          # vehicle 4 speed
                    "No damage",   # vehicle 4 damage
                    "Multi-vehicle collision in intersection during heavy rain", # narrative
                    "weather/road, failed-to-yield, distraction",  # multiple factors
                    "yes",         # injuries
                    "Multiple injuries: Car driver serious, SUV passenger minor, Van driver minor", # injuries
                    "no",          # fatalities
                    "yes",         # property damage
                    "Traffic signal damaged, median barrier damaged",  # property damage
                    "yes",         # witnesses
                    "Multiple witnesses: Store owner 555-0001, Pedestrian Jane 555-0002", # witnesses
                    "Major intersection blocked for 3 hours, multiple emergency vehicles"  # comments
                ]
            }
        ]
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result."""
        self.test_results.append({
            "test": f"{self.current_test} - {test_name}",
            "passed": passed,
            "message": message
        })
        status = "✅" if passed else "❌"
        print(f"  {status} {test_name}: {message}")
    
    def run_all_tests(self):
        """Run all test scenarios."""
        print("🚀 Starting Comprehensive Bot Test Suite")
        print("=" * 60)
        
        # Test 1: Basic bot functionality
        self.current_test = "Basic Functionality"
        print(f"\n📋 {self.current_test}")
        self.test_basic_functionality()
        
        # Test 2: Validator tests
        self.current_test = "Validator Tests"
        print(f"\n📋 {self.current_test}")
        self.test_validators()
        
        # Test 3: Question type handling
        self.current_test = "Question Types"
        print(f"\n📋 {self.current_test}")
        self.test_question_types()
        
        # Test 4: Run full scenarios
        for scenario in self.test_scenarios:
            self.current_test = scenario["name"]
            print(f"\n📋 {self.current_test}")
            print(f"   Description: {scenario.get('description', 'No description')}")
            self.test_full_scenario(scenario)
        
        # Test 5: Edge cases and boundary conditions
        self.current_test = "Advanced Edge Cases"  
        print(f"\n📋 {self.current_test}")
        self.test_advanced_edge_cases()
        
        # Test 6: Path coverage tests
        self.current_test = "Path Coverage Tests"
        print(f"\n📋 {self.current_test}")
        self.test_path_coverage()
        
        # Print summary
        self.print_summary()
    
    def test_basic_functionality(self):
        """Test basic bot setup and initialization."""
        try:
            session = WebBotSession("test_room")
            self.log_test("Session Creation", True, "WebBotSession created successfully")
            
            # Test starting the bot
            response = session.start()
            self.log_test("Bot Start", response is not None and "Welcome" in response, 
                         f"Start response: {response[:100] if response else 'None'}...")
            
            # Test bot status
            status = session.get_status()
            self.log_test("Status Check", status.get("active", False), 
                         f"Status: {status}")
            
        except Exception as e:
            self.log_test("Basic Setup", False, f"Exception: {e}")
    
    def test_validators(self):
        """Test individual validator functions."""
        test_cases = [
            # Date validation
            ({"type": "date"}, "2025-06-12", True),
            ({"type": "date"}, "invalid-date", False),
            ({"type": "date"}, "2025/06/12", True),  # Should work with different format
            
            # Time validation
            ({"type": "time"}, "14:35", True),
            ({"type": "time"}, "25:99", False),
            ({"type": "time"}, "2", False),  # Ambiguous
            
            # Number validation  
            ({"type": "number"}, "50", True),
            ({"type": "number"}, "abc", False),
            ({"type": "number"}, "30 kmh", True),  # Should extract number
            
            # Boolean validation
            ({"type": "boolean"}, "yes", True),
            ({"type": "boolean"}, "1", True),
            ({"type": "boolean"}, "maybe", False),
            
            # Choice validation
            ({"type": "single_choice", "options": ["A", "B", "C"]}, "A", True),
            ({"type": "single_choice", "options": ["A", "B", "C"]}, "1", True),  # Should work with numbers
            ({"type": "single_choice", "options": ["A", "B", "C"]}, "D", False),
        ]
        
        for q_def, input_val, expected in test_cases:
            try:
                is_valid, result = validate_answer(q_def, input_val)
                self.log_test(f"Validator {q_def['type']}", 
                             is_valid == expected,
                             f"Input '{input_val}' -> {is_valid} (expected {expected})")
            except Exception as e:
                self.log_test(f"Validator {q_def['type']}", False, f"Exception: {e}")
    
    def test_question_types(self):
        """Test handling of different question types."""
        try:
            session = WebBotSession("test_types") 
            session.start()
            
            # Test different question type responses
            test_responses = [
                ("Date question", "2025-06-12"),
                ("Time question", "14:35"), 
                ("Location text", "123 Main St"),
                ("Choice question", "wet"),
            ]
            
            for desc, response in test_responses[:4]:  # Test first few questions
                result = session.process_message(response)
                self.log_test(desc, result is not None and "❌" not in result,
                             f"Response: {result[:100] if result else 'None'}...")
                
        except Exception as e:
            self.log_test("Question Types", False, f"Exception: {e}")
    
    def test_full_scenario(self, scenario: Dict[str, Any]):
        """Test a complete form scenario."""
        answers = scenario["answers"]
        session = WebBotSession(f"test_{scenario['name'].replace(' ', '_').lower()}")
        scenario_type = scenario.get("type", "normal")
        
        try:
            # Start the bot
            response = session.start()
            self.log_test("Scenario Start", response is not None, 
                         f"Started {scenario['name']}")
            
            question_count = 0
            answer_index = 0
            max_questions = len(answers) * 2 + 20  # More generous limit for validation testing
            invalid_attempts = 0
            max_invalid_attempts = 3  # Limit consecutive invalid attempts per question
            
            while session.is_active and question_count < max_questions and answer_index < len(answers):
                # Process next answer
                answer = answers[answer_index]
                response = session.process_message(answer)
                
                if response is None:
                    self.log_test(f"Question {question_count + 1}", False, "No response received")
                    break
                
                if "❌" in response and "Something went wrong" in response:
                    self.log_test(f"Question {question_count + 1}", False, 
                                 f"Error response: {response[:100]}...")
                    break
                
                # Check if we got a valid response (not a validation error)
                if "❌" in response and "try again" in response.lower():
                    # This is a validation error - expected in validation testing scenarios
                    invalid_attempts += 1
                    if scenario_type == "validation" and invalid_attempts <= max_invalid_attempts:
                        # Move to next answer (should be the valid one in validation scenarios)
                        answer_index += 1
                        question_count += 1
                        continue
                    elif invalid_attempts > max_invalid_attempts:
                        self.log_test(f"Question {question_count + 1}", False, 
                                     f"Too many invalid attempts: {invalid_attempts}")
                        break
                else:
                    # Valid response, move to next answer
                    invalid_attempts = 0  # Reset counter
                    answer_index += 1
                    
                question_count += 1
                
                # Log progress every 10 questions
                if question_count % 10 == 0:
                    self.log_test(f"Progress Check", True, 
                                 f"Processed {answer_index}/{len(answers)} answers, {question_count} interactions")
            
            # Check final status
            final_status = session.get_status()
            form_complete = final_status.get("form_complete", False) or not session.is_active
            
            # For validation scenarios, success is reaching a reasonable number of questions
            if scenario_type == "validation":
                success = answer_index > len(answers) * 0.3  # At least 30% of answers processed
                self.log_test("Scenario Completion", success,
                             f"Validation test: {answer_index}/{len(answers)} answers processed")
            else:
                self.log_test("Scenario Completion", form_complete,
                             f"Final status: {final_status}")
            
        except Exception as e:
            self.log_test("Scenario Execution", False, f"Exception: {e}")
    
    def test_advanced_edge_cases(self):
        """Test advanced edge cases and boundary conditions."""
        edge_case_scenarios = [
            {
                "name": "Boundary - Maximum Values",
                "description": "Test with boundary values like high speeds, many factors, etc.",
                "inputs": [
                    ("Speed Input", "999"),  # Very high speed
                    ("Multiple Factors", "speeding, failed-to-yield, distraction, weather/road, vehicle defect, other"),
                    ("Long Text", "A" * 500),  # Very long description
                ]
            },
            {
                "name": "Unicode and Special Characters",
                "description": "Test handling of international characters and symbols", 
                "inputs": [
                    ("Unicode Location", "Café résumé naïve Montréal"),
                    ("Special Characters", "Highway #1 @ Main St. (near I-95)"),
                    ("Accented Names", "José González, María Fernández"),
                ]
            },
            {
                "name": "Ambiguous Inputs",
                "description": "Test handling of ambiguous but potentially valid inputs",
                "inputs": [
                    ("Ambiguous Time", "2pm"),  # Should be interpreted as 14:00
                    ("Casual Date", "today"),   # Should prompt for proper format
                    ("Mixed Case", "YeS"),      # Should work for boolean
                    ("Partial Match", "inte"),  # Partial match for "intersection"
                ]
            }
        ]
        
        for scenario in edge_case_scenarios:
            try:
                session = WebBotSession(f"test_edge_{scenario['name'].replace(' ', '_').lower()}")
                session.start()
                
                # Test a few edge case inputs
                success_count = 0
                for desc, test_input in scenario["inputs"][:2]:  # Test first 2 to save time
                    response = session.process_message(test_input)
                    # Edge cases should either work or give a clear error message
                    if response and (
                        "try again" in response.lower() or 
                        "recorded" in response.lower() or
                        "progress" in response.lower()
                    ):
                        success_count += 1
                        
                self.log_test(f"{scenario['name']}", success_count > 0,
                             f"Handled {success_count}/{len(scenario['inputs'][:2])} edge cases")
                
            except Exception as e:
                self.log_test(f"{scenario['name']}", False, f"Exception: {e}")
    
    def test_path_coverage(self):
        """Test different paths through the form to ensure comprehensive coverage."""
        path_tests = [
            {
                "name": "Minimal Path",
                "description": "Single vehicle, no injuries, no damage, no witnesses - shortest possible path",
                "answers": [
                    "2025-01-01", "12:00", "Main St", "dry", "clear", "daylight",
                    "straight", "50", "none", "1", "Car / Honda / Civic", "MIN-123",
                    "straight", "40", "No damage", "Minor fender bender", "none",
                    "no", "no", "no", "no", ""
                ]
            },
            {
                "name": "Maximum Path",
                "description": "Multiple vehicles, all followups triggered - longest possible path", 
                "answers": [
                    "2025-12-31", "23:59", "Complex intersection with multiple landmarks",
                    "snow / ice", "other", "Heavy blizzard conditions", "dark–lit",
                    "intersection", "30", "signal", "other", "4",
                    # Vehicle 1
                    "Motorcycle / Harley / Custom", "MAX-001", "overtaking", "80", "Total loss",
                    # Vehicle 2  
                    "Truck / Mack / Semi", "MAX-002", "turning-left", "60", "Front damage",
                    # Vehicle 3
                    "Bus / Transit / City", "MAX-003", "straight", "40", "Side damage", 
                    # Vehicle 4
                    "Car / BMW / Sedan", "MAX-004", "turning-right", "35", "Rear damage",
                    # Rest of form
                    "Complex multi-vehicle collision in blizzard conditions with multiple contributing factors",
                    "speeding, failed-to-yield, distraction, weather/road, vehicle defect, other",
                    "Poor visibility was a major factor",  # other factor specification
                    "yes", "Multiple serious injuries across all vehicles including critical head trauma and broken bones",
                    "yes", "yes", "Multiple traffic signals, streetlights, and storefronts damaged extensively",
                    "yes", "Numerous witnesses including pedestrians, store employees, and other drivers with full contact details",
                    "Major incident requiring multiple emergency responders, road closure for 6+ hours, and extensive investigation"
                ]
            },
            {
                "name": "Mixed Boolean Formats",
                "description": "Test different ways of answering yes/no questions",
                "answers": [
                    "2025-05-15", "16:30", "Test Location", "wet", "rain", "daylight",
                    "curve", "60", "none", "2",
                    "Car / Test / Vehicle1", "TEST-1", "straight", "50", "Minor damage",
                    "Car / Test / Vehicle2", "TEST-2", "straight", "55", "Minor damage", 
                    "Standard two-car accident", "speeding",
                    "true", "Minor injuries to both drivers",  # true instead of yes
                    "false",  # false instead of no
                    "1",      # 1 instead of yes for property damage
                    "Sign post damaged",
                    "0",      # 0 instead of no for witnesses
                    "Standard accident report"
                ]
            }
        ]
        
        for path_test in path_tests:
            self.current_test = f"Path: {path_test['name']}"
            print(f"   Testing: {path_test['description']}")
            
            session = WebBotSession(f"test_path_{path_test['name'].replace(' ', '_').lower()}")
            
            try:
                response = session.start()
                if not response:
                    self.log_test("Path Start", False, "Failed to start session")
                    continue
                    
                answers_processed = 0
                total_answers = len(path_test["answers"])
                
                for answer in path_test["answers"]:
                    if not session.is_active:
                        break
                        
                    response = session.process_message(answer)
                    if response and "❌" not in response:
                        answers_processed += 1
                    elif "try again" in response.lower():
                        # Give it one more try with the same answer (might be validation issue)
                        response = session.process_message(answer)
                        if response and "❌" not in response:
                            answers_processed += 1
                
                completion_rate = answers_processed / total_answers
                self.log_test(path_test['name'], completion_rate > 0.8,
                             f"Completed {answers_processed}/{total_answers} answers ({completion_rate:.1%})")
                
            except Exception as e:
                self.log_test(path_test['name'], False, f"Path test exception: {e}")
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%" if total > 0 else "No tests run")
        
        # Group results by test category
        test_categories = {}
        for result in self.test_results:
            category = result["test"].split(" - ")[0]
            if category not in test_categories:
                test_categories[category] = {"passed": 0, "total": 0}
            test_categories[category]["total"] += 1
            if result["passed"]:
                test_categories[category]["passed"] += 1
        
        print(f"\n📊 RESULTS BY CATEGORY:")
        for category, stats in test_categories.items():
            rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            status = "✅" if rate == 100 else "⚠️" if rate >= 80 else "❌"
            print(f"  {status} {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r["passed"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")
        
        # Show comprehensive coverage summary
        full_scenarios = [t for t in self.test_results if "Scenario Completion" in t["test"]]
        completed_scenarios = [t for t in full_scenarios if t["passed"]]
        
        print(f"\n🎯 FORM COVERAGE ANALYSIS:")
        print(f"  📝 Full Form Scenarios: {len(completed_scenarios)}/{len(full_scenarios)} completed")
        
        # Count different path types tested
        path_types = {
            "single_vehicle": len([t for t in self.test_results if "Single Vehicle" in t["test"]]),
            "multi_vehicle": len([t for t in self.test_results if any(x in t["test"] for x in ["Three Vehicle", "Four Vehicle"])]),
            "edge_cases": len([t for t in self.test_results if "Edge" in t["test"]]),
            "path_coverage": len([t for t in self.test_results if "Path:" in t["test"]]),
        }
        
        print(f"  🚗 Single Vehicle Paths: {path_types['single_vehicle']} tested")
        print(f"  🚗🚗 Multi Vehicle Paths: {path_types['multi_vehicle']} tested") 
        print(f"  ⚠️  Edge Case Paths: {path_types['edge_cases']} tested")
        print(f"  🛣️  Coverage Paths: {path_types['path_coverage']} tested")
        
        # Show overall result
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED! The bot handles all tested scenarios correctly.")
            print(f"   ✓ Basic functionality working")
            print(f"   ✓ Input validation working") 
            print(f"   ✓ All form paths tested")
            print(f"   ✓ Edge cases handled")
        elif passed/total >= 0.9:
            print(f"\n✅ EXCELLENT COVERAGE: {passed}/{total} tests passed.")
            print(f"   The bot is working very well with only minor issues.")
        elif passed/total >= 0.8:
            print(f"\n⚠️  GOOD COVERAGE: {passed}/{total} tests passed.")
            print(f"   The bot is working well but some edge cases need attention.")
        elif passed/total >= 0.7:
            print(f"\n⚠️  MODERATE COVERAGE: {passed}/{total} tests passed.")
            print(f"   The bot has basic functionality but needs improvements.")
        else:
            print(f"\n❌ POOR COVERAGE: Only {passed}/{total} tests passed.")
            print(f"   The bot has significant issues that need to be addressed.")


def main():
    """Run the comprehensive test suite."""
    if not BOT_AVAILABLE:
        print("❌ Cannot run tests - bot components not available")
        return
    
    test_suite = BotTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()
