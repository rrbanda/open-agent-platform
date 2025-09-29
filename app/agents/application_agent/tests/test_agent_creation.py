"""
ApplicationAgent Creation Tests

This module tests the creation and basic functionality of the ApplicationAgent.
Tests cover agent instantiation, configuration, and basic conversational capabilities.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

try:
    from app.agents.application_agent import create_application_agent
    from utils import initialize_connection
    
    # Test agent creation
    print("🏗️ Testing ApplicationAgent Creation...")
    
    # Initialize Neo4j connection
    initialize_connection()
    
    # Test 1: Basic agent creation
    print("1. Testing basic agent creation...")
    agent = create_application_agent()
    assert agent is not None, "Agent creation should return a valid agent object"
    print("    Agent created successfully")
    
    # Test 2: Agent has required attributes
    print("2. Testing agent attributes...")
    assert hasattr(agent, 'invoke'), "Agent should have invoke method"
    assert hasattr(agent, 'stream'), "Agent should have stream method"
    print("    Agent has required methods")
    
    # Test 3: Basic conversation test
    print("3. Testing basic conversation...")
    test_input = {"messages": [{"role": "user", "content": "Hello, I want to apply for a mortgage"}]}
    result = agent.invoke(test_input)
    assert "messages" in result, "Agent should return messages in response"
    assert len(result["messages"]) > 1, "Agent should respond with at least one message"
    print("    Basic conversation working")
    
    # Test 4: Response content validation
    print("4. Testing response content...")
    response_content = str(result["messages"][-1])
    assert len(response_content) > 10, "Response should have meaningful content"
    print("    Response has meaningful content")
    
    print("\n🎉 All agent creation tests passed!")
    
except Exception as e:
    print(f"\n Agent creation test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def run_agent_creation_tests():
    """
    Run ApplicationAgent creation tests and return success status.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        # Initialize database connection
        initialize_connection()
        
        # Test agent creation
        agent = create_application_agent()
        if agent is None:
            return False
        
        # Test basic functionality
        test_input = {"messages": [{"role": "user", "content": "Hello"}]}
        result = agent.invoke(test_input)
        
        # Validate response structure
        if "messages" not in result or len(result["messages"]) <= 1:
            return False
        
        return True
        
    except Exception as e:
        print(f"Agent creation test error: {e}")
        return False


if __name__ == "__main__":
    # When run directly, execute the tests
    pass
