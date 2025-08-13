#!/usr/bin/env python3
"""
Quick test for the AI bot implementation.
Run this to verify the AI bot works before integration.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "accident_report"))

def test_ai_bot():
    print("🧪 Testing AI Bot Implementation")
    print("=" * 50)
    
    # Test 1: Import check
    print("\n1️⃣ Testing imports...")
    try:
        from backend.accident_report.LLM.rigid_AI_bot import AIBotWorkflow
        from backend.accident_report.LLM.llm_config import llm
        print("✅ AI Bot imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: LLM configuration
    print("\n2️⃣ Testing LLM configuration...")
    try:
        # Simple test call
        response = llm.invoke("Hello, this is a test.")
        print(f"✅ LLM response: {response.content[:50]}...")
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False
    
    # Test 3: Questions file
    print("\n3️⃣ Testing questions file...")
    questions_file = BACKEND_DIR / "backend" / "accident_report" / "questionnaire" / "questions.json"
    if questions_file.exists():
        print(f"✅ Questions file found: {questions_file}")
    else:
        print(f"❌ Questions file not found: {questions_file}")
        return False
    
    # Test 4: AI Bot initialization
    print("\n4️⃣ Testing AI Bot initialization...")
    try:
        bot = AIBotWorkflow(str(questions_file), interactive=False)
        print("✅ AI Bot workflow initialized")
    except Exception as e:
        print(f"❌ AI Bot initialization failed: {e}")
        return False
    
    # Test 5: Graph compilation
    print("\n5️⃣ Testing graph compilation...")
    try:
        graph = bot.compile_graph()
        print("✅ Graph compiled successfully")
    except Exception as e:
        print(f"❌ Graph compilation failed: {e}")
        return False
    
    # Test 6: Simulated conversation
    print("\n6️⃣ Testing simulated conversation...")
    try:
        config = {"configurable": {"thread_id": "test_session"}, "recursion_limit": 10}
        
        # Start the bot
        events = list(graph.stream({}, config=config))
        state = graph.get_state(config).values
        
        first_question = state.get("rephrased_question", "No question found")
        print(f"✅ First question: {first_question[:100]}...")
        
        # Simulate user input
        from langchain_core.messages import HumanMessage
        updated_state = {
            **state,
            "messages": state.get("messages", []) + [HumanMessage(content="today")]
        }
        
        graph.update_state(config, updated_state)
        list(graph.stream(None, config=config))
        
        new_state = graph.get_state(config).values
        next_output = (new_state.get("clarifying_question") or 
                      new_state.get("rephrased_question") or 
                      "No response")
        print(f"✅ Bot response to 'today': {next_output[:100]}...")
        
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 All tests passed! AI Bot is ready to use.")
    return True

if __name__ == "__main__":
    success = test_ai_bot()
    sys.exit(0 if success else 1)
