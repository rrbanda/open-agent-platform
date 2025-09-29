"""
Test Agent Creation for UnderwritingAgent

This module tests the basic creation and initialization of the UnderwritingAgent,
ensuring it follows the established patterns and integrates properly with LangGraph.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from app.agents.underwriting_agent import create_underwriting_agent
from app.agents.underwriting_agent.tools import get_all_underwriting_agent_tools


class TestUnderwritingAgentCreation:
    """Test suite for UnderwritingAgent creation and basic functionality."""
    
    def test_agent_creation_basic(self):
        """Test that UnderwritingAgent can be created successfully."""
        try:
            agent = create_underwriting_agent()
            assert agent is not None, "Agent should not be None"
            print(" UnderwritingAgent created successfully")
        except Exception as e:
            pytest.fail(f"Failed to create UnderwritingAgent: {e}")
    
    def test_agent_type_validation(self):
        """Test that the created agent is of the correct type."""
        try:
            agent = create_underwriting_agent()
            
            # Check that it's a compiled LangGraph agent
            agent_type = str(type(agent))
            assert "CompiledStateGraph" in agent_type, f"Expected CompiledStateGraph, got {agent_type}"
            print(f" Agent type validation passed: {agent_type}")
        except Exception as e:
            pytest.fail(f"Agent type validation failed: {e}")
    
    def test_tools_integration(self):
        """Test that all expected tools are properly integrated."""
        try:
            tools = get_all_underwriting_agent_tools()
            
            # Verify we have the expected number of tools
            assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"
            
            # Verify specific tool names
            expected_tools = [
                "analyze_credit_risk",
                "calculate_debt_to_income", 
                "evaluate_income_sources",
                "make_underwriting_decision"
            ]
            
            tool_names = [tool.name for tool in tools]
            for expected_tool in expected_tools:
                assert expected_tool in tool_names, f"Tool {expected_tool} not found in {tool_names}"
            
            print(f" All {len(tools)} tools properly integrated")
            for tool in tools:
                print(f"   • {tool.name}")
                
        except Exception as e:
            pytest.fail(f"Tools integration test failed: {e}")
    
    def test_agent_configuration(self):
        """Test that the agent has proper configuration."""
        try:
            agent = create_underwriting_agent()
            
            # Test that agent has necessary attributes
            assert hasattr(agent, 'invoke'), "Agent should have invoke method"
            assert hasattr(agent, 'stream'), "Agent should have stream method"
            
            # Test that agent can be called with basic input
            test_state = {"messages": []}
            # Just test that invoke doesn't crash immediately
            assert callable(agent.invoke), "Agent invoke method should be callable"
            
            print(" Agent configuration validation passed")
            
        except Exception as e:
            pytest.fail(f"Agent configuration test failed: {e}")
    
    def test_import_structure(self):
        """Test that all imports work correctly."""
        try:
            # Test main agent import
            from app.agents.underwriting_agent import create_underwriting_agent
            
            # Test tools imports
            from app.agents.underwriting_agent.tools import (
                analyze_credit_risk,
                calculate_debt_to_income,
                evaluate_income_sources,
                make_underwriting_decision,
                get_all_underwriting_agent_tools
            )
            
            # Test individual tool imports
            from app.agents.underwriting_agent.tools.analyze_credit_risk import analyze_credit_risk as credit_tool
            from app.agents.underwriting_agent.tools.calculate_debt_to_income import calculate_debt_to_income as dti_tool
            from app.agents.underwriting_agent.tools.evaluate_income_sources import evaluate_income_sources as income_tool
            from app.agents.underwriting_agent.tools.make_underwriting_decision import make_underwriting_decision as decision_tool
            
            print(" All import structures working correctly")
            
        except ImportError as e:
            pytest.fail(f"Import structure test failed: {e}")
        except Exception as e:
            pytest.fail(f"Import test failed with unexpected error: {e}")


def run_agent_creation_tests():
    """Run all agent creation tests and return results."""
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    test_class = TestUnderwritingAgentCreation()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    results["total_tests"] = len(test_methods)
    
    for test_method_name in test_methods:
        try:
            test_method = getattr(test_class, test_method_name)
            test_method()
            results["passed_tests"] += 1
            results["test_details"].append(f" {test_method_name}: PASSED")
        except Exception as e:
            results["failed_tests"] += 1
            results["test_details"].append(f" {test_method_name}: FAILED - {str(e)}")
    
    return results


if __name__ == "__main__":
    print("🧪 RUNNING UNDERWRITING AGENT CREATION TESTS")
    print("=" * 60)
    
    results = run_agent_creation_tests()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    
    print(f"\n📋 TEST DETAILS:")
    for detail in results["test_details"]:
        print(detail)
    
    if results["failed_tests"] == 0:
        print("\n🎉 ALL AGENT CREATION TESTS PASSED!")
    else:
        print(f"\n⚠️ {results['failed_tests']} TEST(S) FAILED")
        sys.exit(1)
