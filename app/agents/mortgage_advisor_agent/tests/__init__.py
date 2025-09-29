"""
MortgageAdvisorAgent Tests Package

This package contains comprehensive tests for the MortgageAdvisorAgent including:
- Agent creation and configuration tests (FUNCTIONALITY)
- Individual tool functionality tests (FUNCTIONALITY)
- Integration tests with Neo4j database (FUNCTIONALITY)
- End-to-end workflow tests (FUNCTIONALITY)
- Professional LLM/Agent evaluations via LangSmith (EVALUATION)

Test Structure:
- test_agent_creation.py: Agent instantiation and configuration tests
- test_tool_validation.py: Tests for each of the 4 tools
- test_prompt_validation.py: Prompt loading and content validation
- test_end_to_end.py: Complete workflow tests
- test_langsmith_evaluations.py: Professional LLM/agent evaluations using LangSmith
- run_all_tests.py: Test runner for functionality tests

Note: Only LangSmith evaluations are used for LLM/agent assessment to avoid misleading custom metrics.
"""

from .test_agent_creation import run_agent_creation_tests
from .test_tool_validation import run_tool_validation_tests
from .test_prompt_validation import run_prompt_validation_tests  
from .test_end_to_end import run_end_to_end_tests
from .test_langsmith_evaluations import run_langsmith_evaluations
from .run_all_tests import run_all_mortgage_advisor_tests, run_quick_smoke_test

__all__ = [
    # Test category runners - FUNCTIONALITY TESTS ONLY
    "run_agent_creation_tests",
    "run_tool_validation_tests",
    "run_prompt_validation_tests",
    "run_end_to_end_tests", 
    
    # Professional LLM/Agent Evaluations - LANGSMITH ONLY
    "run_langsmith_evaluations",
    
    # Main test runner
    "run_all_mortgage_advisor_tests",
    "run_quick_smoke_test"
]
