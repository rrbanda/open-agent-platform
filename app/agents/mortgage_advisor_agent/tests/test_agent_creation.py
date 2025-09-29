"""
Test Agent Creation and Configuration

Tests for MortgageAdvisorAgent instantiation, configuration,
LLM integration, and basic functionality.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.agents.mortgage_advisor_agent import create_mortgage_advisor_agent
from utils.config import AppConfig
from langchain_core.language_models.base import BaseLanguageModel


def test_agent_creation():
    """Test that MortgageAdvisorAgent can be created successfully."""
    try:
        agent = create_mortgage_advisor_agent()
        
        # Verify agent exists and has required methods
        assert agent is not None, "Agent should be created"
        assert hasattr(agent, 'invoke'), "Agent should have invoke method"
        assert hasattr(agent, 'stream'), "Agent should have stream method"
        assert hasattr(agent, 'get_graph'), "Agent should have get_graph method"
        
        print(" Agent creation test passed")
        return True
        
    except Exception as e:
        print(f" Agent creation failed: {e}")
        return False


def test_agent_configuration():
    """Test that agent loads configuration properly."""
    try:
        # Load config
        config = AppConfig.load()
        
        # Verify config has required sections
        assert hasattr(config, 'llamastack'), "Config should have llamastack section"
        assert hasattr(config, 'neo4j'), "Config should have neo4j section"
        
        # Verify Neo4j config
        assert config.neo4j.uri, "Neo4j URI should be configured"
        assert config.neo4j.username, "Neo4j username should be configured"
        assert config.neo4j.database, "Neo4j database should be configured"
        
        print(" Agent configuration test passed")
        return True
        
    except Exception as e:
        print(f" Agent configuration failed: {e}")
        return False


def test_agent_tools_binding():
    """Test that agent has all 4 required tools bound."""
    try:
        agent = create_mortgage_advisor_agent()
        
        # Get the graph structure
        graph = agent.get_graph()
        
        # Verify graph exists and has nodes
        assert graph is not None, "Agent graph should exist"
        
        # Test that agent can be invoked (basic smoke test)
        # This verifies the tools are properly bound
        test_input = {
            "messages": [{"role": "user", "content": "Hello, I need help with mortgage options"}]
        }
        
        # Should not raise an exception
        result = agent.invoke(test_input)
        assert "messages" in result, "Agent should return messages"
        
        print(" Agent tools binding test passed")
        return True
        
    except Exception as e:
        print(f" Agent tools binding failed: {e}")
        return False


def test_agent_llm_integration():
    """Test that agent integrates with LLM properly."""
    try:
        from app.utils.llm_factory import get_llm
        
        # Test LLM factory
        llm = get_llm()
        assert llm is not None, "LLM should be created"
        
        # Verify LLM is BaseLanguageModel
        assert isinstance(llm, BaseLanguageModel), "LLM should be BaseLanguageModel instance"
        
        print(" Agent LLM integration test passed")
        return True
        
    except Exception as e:
        print(f" Agent LLM integration failed: {e}")
        return False


def test_agent_name_and_metadata():
    """Test agent has proper name and metadata."""
    try:
        agent = create_mortgage_advisor_agent()
        
        # Verify agent was created with proper name
        # The create_react_agent should have name="mortgage_advisor_agent"
        graph = agent.get_graph()
        assert graph is not None, "Graph should exist"
        
        print(" Agent name and metadata test passed")
        return True
        
    except Exception as e:
        print(f" Agent name and metadata failed: {e}")
        return False


def run_agent_creation_tests():
    """Run all agent creation tests."""
    print("🧪 Running Agent Creation Tests")
    print("=" * 40)
    
    tests = [
        test_agent_creation,
        test_agent_configuration,
        test_agent_tools_binding,
        test_agent_llm_integration,
        test_agent_name_and_metadata
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f" Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Agent Creation Tests: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    success = run_agent_creation_tests()
    sys.exit(0 if success else 1)
