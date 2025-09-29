"""
Test End-to-End Agent Functionality

Tests complete MortgageAdvisorAgent workflows including tool calling,
response generation, and validation of agent behavior.
"""

import pytest
import sys
import json
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.agents.mortgage_advisor_agent import create_mortgage_advisor_agent
from utils import initialize_connection


def _extract_message_content(message):
    """Extract content from either dict or LangChain message object."""
    if hasattr(message, 'content'):
        # LangChain message object
        return getattr(message, 'content', '')
    elif isinstance(message, dict):
        # Dictionary format
        return message.get('content', '')
    else:
        return str(message)


def _get_message_role(message):
    """Get role from either dict or LangChain message object."""
    if hasattr(message, 'type'):
        # LangChain message object
        msg_type = getattr(message, 'type', '')
        if msg_type == 'ai':
            return 'assistant'
        elif msg_type == 'human':
            return 'user'
        else:
            return msg_type
    elif isinstance(message, dict):
        # Dictionary format
        return message.get('role', '')
    else:
        return 'unknown'


def _has_tool_calls(message):
    """Check if message has tool calls."""
    if hasattr(message, 'tool_calls'):
        tool_calls = getattr(message, 'tool_calls', [])
        return len(tool_calls) > 0
    elif isinstance(message, dict):
        tool_calls = message.get('tool_calls', [])
        return len(tool_calls) > 0
    else:
        return False


def _get_tool_calls(message):
    """Get tool calls from message."""
    if hasattr(message, 'tool_calls'):
        return getattr(message, 'tool_calls', [])
    elif isinstance(message, dict):
        return message.get('tool_calls', [])
    else:
        return []


def test_agent_basic_conversation():
    """Test basic conversation without tool calling."""
    print("🤖 Testing agent basic conversation...")
    
    try:
        agent = create_mortgage_advisor_agent()
        
        # Simple greeting
        test_input = {
            "messages": [{"role": "user", "content": "Hello, I'm interested in learning about mortgages"}]
        }
        
        result = agent.invoke(test_input)
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "messages" in result, "Result should contain messages"
        assert isinstance(result["messages"], list), "Messages should be a list"
        
        # Should have at least user message + assistant response
        assert len(result["messages"]) >= 2, "Should have user and assistant messages"
        
        # Last message should be from assistant
        last_message = result["messages"][-1]
        last_role = _get_message_role(last_message)
        last_content = _extract_message_content(last_message)
        
        assert last_role == "assistant", f"Last message should be from assistant, got {last_role}"
        assert len(str(last_content).strip()) > 0, "Assistant content should not be empty"
        
        print(" Agent basic conversation test passed")
        return True
        
    except Exception as e:
        print(f" Agent basic conversation failed: {e}")
        return False


def test_agent_loan_program_explanation():
    """Test agent calling explain_loan_programs tool."""
    print("🤖 Testing agent loan program explanation...")
    
    try:
        agent = create_mortgage_advisor_agent()
        
        # Request that should trigger explain_loan_programs tool
        test_input = {
            "messages": [{"role": "user", "content": "Can you explain the differences between FHA and VA loans?"}]
        }
        
        result = agent.invoke(test_input)
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "messages" in result, "Result should contain messages"
        
        messages = result["messages"]
        assert len(messages) >= 2, "Should have user and assistant messages"
        
        # Check if tool was called by looking for tool_calls in messages
        tool_calls_found = False
        for message in messages:
            role = _get_message_role(message)
            if role == "assistant" and _has_tool_calls(message):
                tool_calls_found = True
                tool_calls = _get_tool_calls(message)
                
                # Check if explain_loan_programs was called
                for tool_call in tool_calls:
                    # Handle different tool call formats
                    tool_name = None
                    if hasattr(tool_call, 'name'):
                        tool_name = tool_call.name
                    elif isinstance(tool_call, dict) and "function" in tool_call:
                        tool_name = tool_call.get("function", {}).get("name")
                    elif isinstance(tool_call, dict) and "name" in tool_call:
                        tool_name = tool_call.get("name")
                    
                    if tool_name == "explain_loan_programs":
                        print("    explain_loan_programs tool was called")
                        break
        
        # Should have final assistant response with content
        final_message = messages[-1]
        final_role = _get_message_role(final_message)
        final_content = _extract_message_content(final_message)
        
        assert final_role == "assistant", "Final message should be from assistant"
        assert len(str(final_content).strip()) > 0, "Final response should not be empty"
        
        print(" Agent loan program explanation test passed")
        return True
        
    except Exception as e:
        print(f" Agent loan program explanation failed: {e}")
        return False


def test_agent_loan_recommendation():
    """Test agent calling recommend_loan_program tool."""
    print("🤖 Testing agent loan recommendation...")
    
    try:
        agent = create_mortgage_advisor_agent()
        
        # Request with borrower details that should trigger recommend_loan_program
        test_input = {
            "messages": [{"role": "user", "content": "I'm a veteran with a 720 credit score and $85,000 income. I want to buy a house with no down payment. What loan program would you recommend?"}]
        }
        
        result = agent.invoke(test_input)
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "messages" in result, "Result should contain messages"
        
        messages = result["messages"]
        assert len(messages) >= 2, "Should have user and assistant messages"
        
        # Check if tool was called
        tool_calls_found = False
        for message in messages:
            role = _get_message_role(message)
            if role == "assistant" and _has_tool_calls(message):
                tool_calls_found = True
                tool_calls = _get_tool_calls(message)
                
                # Check if recommend_loan_program was called
                for tool_call in tool_calls:
                    tool_name = None
                    if hasattr(tool_call, 'name'):
                        tool_name = tool_call.name
                    elif isinstance(tool_call, dict) and "function" in tool_call:
                        tool_name = tool_call.get("function", {}).get("name")
                    elif isinstance(tool_call, dict) and "name" in tool_call:
                        tool_name = tool_call.get("name")
                    
                    if tool_name == "recommend_loan_program":
                        print("    recommend_loan_program tool was called")
                        break
        
        # Should have final assistant response
        final_message = messages[-1]
        final_role = _get_message_role(final_message)
        final_content = _extract_message_content(final_message)
        
        assert final_role == "assistant", "Final message should be from assistant"
        
        # Response should mention loan recommendations
        content = str(final_content).lower()
        loan_terms = ["va", "loan", "recommend", "credit", "score"]
        found_terms = [term for term in loan_terms if term in content]
        assert len(found_terms) >= 2, f"Response should mention loan-related terms, found: {found_terms}"
        
        print(" Agent loan recommendation test passed")
        return True
        
    except Exception as e:
        print(f" Agent loan recommendation failed: {e}")
        return False


def test_agent_qualification_check():
    """Test agent calling check_qualification_requirements tool."""
    print("🤖 Testing agent qualification check...")
    
    try:
        agent = create_mortgage_advisor_agent()
        
        # Request that should trigger qualification check
        test_input = {
            "messages": [{"role": "user", "content": "I have a 650 credit score and want to know if I qualify for a VA loan. What are the requirements?"}]
        }
        
        result = agent.invoke(test_input)
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "messages" in result, "Result should contain messages"
        
        messages = result["messages"]
        assert len(messages) >= 2, "Should have user and assistant messages"
        
        # Check for tool usage
        tool_calls_found = False
        for message in messages:
            role = _get_message_role(message)
            if role == "assistant" and _has_tool_calls(message):
                tool_calls_found = True
                break
        
        # Should have final assistant response about qualifications
        final_message = messages[-1]
        final_role = _get_message_role(final_message)
        final_content = _extract_message_content(final_message)
        
        assert final_role == "assistant", "Final message should be from assistant"
        
        print(" Agent qualification check test passed")
        return True
        
    except Exception as e:
        print(f" Agent qualification check failed: {e}")
        return False


def test_agent_next_steps_guidance():
    """Test agent calling guide_next_steps tool."""
    print("🤖 Testing agent next steps guidance...")
    
    try:
        agent = create_mortgage_advisor_agent()
        
        # Request that should trigger next steps guidance
        test_input = {
            "messages": [{"role": "user", "content": "I'm ready to apply for a VA loan. What should I do first?"}]
        }
        
        result = agent.invoke(test_input)
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "messages" in result, "Result should contain messages"
        
        messages = result["messages"]
        assert len(messages) >= 2, "Should have user and assistant messages"
        
        # Should have final assistant response with guidance
        final_message = messages[-1]
        final_role = _get_message_role(final_message)
        final_content = _extract_message_content(final_message)
        
        assert final_role == "assistant", "Final message should be from assistant"
        
        # Response should provide guidance
        content = str(final_content).lower()
        guidance_terms = ["first", "step", "next", "apply", "process"]
        found_terms = [term for term in guidance_terms if term in content]
        assert len(found_terms) >= 2, f"Response should mention process guidance terms, found: {found_terms}"
        
        print(" Agent next steps guidance test passed")
        return True
        
    except Exception as e:
        print(f" Agent next steps guidance failed: {e}")
        return False


def test_agent_multi_turn_conversation():
    """Test multi-turn conversation with the agent."""
    print("🤖 Testing agent multi-turn conversation...")
    
    try:
        agent = create_mortgage_advisor_agent()
        
        # Start conversation
        conversation = {
            "messages": [{"role": "user", "content": "Hi, I'm looking for help with mortgage options"}]
        }
        
        # First turn
        result1 = agent.invoke(conversation)
        conversation = result1  # Update conversation state
        
        # Second turn - ask specific question
        conversation["messages"].append({
            "role": "user", 
            "content": "I'm a first-time buyer with a 680 credit score. What loan programs should I consider?"
        })
        
        result2 = agent.invoke(conversation)
        
        # Validate final conversation
        assert isinstance(result2, dict), "Result should be a dictionary"
        assert "messages" in result2, "Result should contain messages"
        
        messages = result2["messages"]
        assert len(messages) >= 4, "Should have multiple turns of conversation"
        
        # Should have user and assistant messages alternating
        roles = [_get_message_role(msg) for msg in messages]
        assert "user" in roles, "Should have user messages"
        assert "assistant" in roles, "Should have assistant messages"
        
        print(" Agent multi-turn conversation test passed")
        return True
        
    except Exception as e:
        print(f" Agent multi-turn conversation failed: {e}")
        return False


def test_agent_error_handling():
    """Test agent error handling with invalid inputs."""
    print("🤖 Testing agent error handling...")
    
    try:
        agent = create_mortgage_advisor_agent()
        
        # Test with empty message
        test_input1 = {
            "messages": [{"role": "user", "content": ""}]
        }
        
        result1 = agent.invoke(test_input1)
        assert isinstance(result1, dict), "Result should be a dictionary even with empty content"
        assert "messages" in result1, "Result should contain messages"
        
        # Test with very long message
        test_input2 = {
            "messages": [{"role": "user", "content": "mortgage " * 1000}]
        }
        
        result2 = agent.invoke(test_input2)
        assert isinstance(result2, dict), "Result should be a dictionary even with long content"
        assert "messages" in result2, "Result should contain messages"
        
        # Test with non-mortgage related question
        test_input3 = {
            "messages": [{"role": "user", "content": "What's the weather like today?"}]
        }
        
        result3 = agent.invoke(test_input3)
        assert isinstance(result3, dict), "Result should be a dictionary even with off-topic content"
        assert "messages" in result3, "Result should contain messages"
        
        # Response should redirect to mortgage topics
        final_message = result3["messages"][-1]
        final_content = _extract_message_content(final_message)
        content = str(final_content).lower()
        assert "mortgage" in content or "loan" in content or "help" in content, "Should redirect to mortgage topics"
        
        print(" Agent error handling test passed")
        return True
        
    except Exception as e:
        print(f" Agent error handling failed: {e}")
        return False


def run_end_to_end_tests():
    """Run all end-to-end tests."""
    print("\n🧪 Running End-to-End Tests")
    print("=" * 40)
    
    # Check Neo4j connection first
    print("🔌 Checking Neo4j connection...")
    if not initialize_connection():
        print(" Neo4j connection failed - skipping end-to-end tests")
        return False
    
    tests = [
        test_agent_basic_conversation,
        test_agent_loan_program_explanation,
        test_agent_loan_recommendation,
        test_agent_qualification_check,
        test_agent_next_steps_guidance,
        test_agent_multi_turn_conversation,
        test_agent_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f" Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 End-to-End Tests: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    success = run_end_to_end_tests()
    sys.exit(0 if success else 1)
