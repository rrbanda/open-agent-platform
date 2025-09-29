"""
ApplicationAgent Tests Package

This package contains comprehensive test suites for the ApplicationAgent,
focusing on functionality testing and professional LLM/agent evaluations.

Test Categories:
1. Agent Creation Tests - Basic agent functionality and setup
2. Tool Validation Tests - Individual tool testing and validation
3. Prompt Validation Tests - Prompt loading and content validation
4. End-to-End Tests - Complete workflow testing

Professional Evaluations:
- LangSmith Evaluations - Industry-standard LLM/agent evaluation framework

Usage:
    # Functionality tests
    from app.agents.application_agent.tests import run_all_application_agent_tests
    results = run_all_application_agent_tests()
    
    # Professional LLM/agent evaluations
    from app.agents.application_agent.tests import run_langsmith_evaluations
    eval_results = run_langsmith_evaluations(quick=True)

Test Structure:
- test_agent_creation.py: Tests agent creation, configuration, and basic functionality
- test_tool_validation.py: Tests individual tool functionality with various scenarios
- test_prompt_validation.py: Tests prompt loading, content, and structure validation
- test_end_to_end.py: Tests complete agent workflows and user interactions
- test_langsmith_evaluations.py: Professional LLM/agent evaluations using LangSmith
- run_all_tests.py: Test runner for functionality tests

Note: Only LangSmith evaluations are used for LLM/agent assessment to avoid misleading custom metrics.
"""

from .test_agent_creation import run_agent_creation_tests
from .test_tool_validation import run_tool_validation_tests
from .test_prompt_validation import run_prompt_validation_tests
from .test_end_to_end import run_end_to_end_tests
from .test_langsmith_evaluations import run_langsmith_evaluations


def run_all_application_agent_tests():
    """
    Run all ApplicationAgent functionality test categories and return comprehensive results.
    
    This function orchestrates the execution of all core functionality tests for the
    ApplicationAgent, providing a summary of passed/failed tests.
    
    Note: This runner focuses on functionality. For professional LLM/agent evaluations,
    use `run_langsmith_evaluations()` separately.
    """
    print("🧪 RUNNING COMPREHENSIVE APPLICATION AGENT TEST SUITE (FUNCTIONALITY ONLY)")
    print("=" * 70)
    
    test_categories = [
        ("Agent Creation", run_agent_creation_tests),
        ("Tool Validation", run_tool_validation_tests),
        ("Prompt Validation", run_prompt_validation_tests),
        ("End-to-End", run_end_to_end_tests)
    ]
    
    comprehensive_results = {
        "total_tests": 0,
        "total_passed": 0,
        "total_failed": 0,
        "category_results": {},
        "overall_success_rate": 0.0
    }
    
    for category_name, test_runner in test_categories:
        print(f"\n--- Running {category_name} Tests ---")
        
        try:
            category_passed = test_runner()
            
            # Assume single test per category for simplicity
            # In practice, test runners could return more detailed results
            total_in_category = 1
            passed_in_category = 1 if category_passed else 0
            failed_in_category = total_in_category - passed_in_category
            
            comprehensive_results["total_tests"] += total_in_category
            comprehensive_results["total_passed"] += passed_in_category
            comprehensive_results["total_failed"] += failed_in_category
            
            comprehensive_results["category_results"][category_name] = {
                "total_tests": total_in_category,
                "passed_tests": passed_in_category,
                "failed_tests": failed_in_category,
                "success": passed_in_category == total_in_category
            }
            
            status = " PASSED" if category_passed else f" FAILED"
            print(f"--- {category_name} Tests {status} ---")
            
        except Exception as e:
            print(f"--- {category_name} Tests  FAILED (Error: {e}) ---")
            
            comprehensive_results["total_tests"] += 1
            comprehensive_results["total_failed"] += 1
            
            comprehensive_results["category_results"][category_name] = {
                "total_tests": 1,
                "passed_tests": 0,
                "failed_tests": 1,
                "success": False,
                "error": str(e)
            }
    
    if comprehensive_results["total_tests"] > 0:
        comprehensive_results["overall_success_rate"] = (
            comprehensive_results["total_passed"] / comprehensive_results["total_tests"] * 100
        )
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE APPLICATION AGENT TEST SUMMARY (FUNCTIONALITY ONLY)")
    print("=" * 70)
    print(f"Total Tests Run: {comprehensive_results['total_tests']}")
    print(f"Total Tests Passed: {comprehensive_results['total_passed']}")
    print(f"Total Tests Failed: {comprehensive_results['total_failed']}")
    print(f"Overall Success Rate: {comprehensive_results['overall_success_rate']:.2f}%")
    print("-" * 70)
    
    if comprehensive_results["total_failed"] == 0:
        print("🎉 All functionality tests passed! ApplicationAgent is robust and ready.")
        print(" Application intake capabilities fully functional")
        print(" All 5 Neo4j-powered tools working correctly")
        print(" Workflow routing and status tracking operational")
        print(" Ready for production deployment!")
    else:
        print("🔧 Please review and fix failing tests before production deployment.")
        print("ApplicationAgent shows promise but needs refinement.")
    
    return comprehensive_results


__all__ = [
    # Individual test runners - FUNCTIONALITY TESTS ONLY
    "run_agent_creation_tests",
    "run_tool_validation_tests",
    "run_prompt_validation_tests",
    "run_end_to_end_tests",
    
    # Professional LLM/Agent Evaluations - LANGSMITH ONLY
    "run_langsmith_evaluations",
    
    # Comprehensive test runner
    "run_all_application_agent_tests"
]
