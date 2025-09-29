"""
UnderwritingAgent Tests Package

This package contains comprehensive test suites for the UnderwritingAgent,
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
    from app.agents.underwriting_agent.tests import run_all_underwriting_agent_tests
    results = run_all_underwriting_agent_tests()
    
    # Professional LLM/agent evaluations
    from app.agents.underwriting_agent.tests import run_langsmith_evaluations
    eval_results = run_langsmith_evaluations(quick=True)

Test Structure:
- test_agent_creation.py: Tests agent creation, configuration, and basic functionality
- test_tool_validation.py: Tests individual tool functionality with various scenarios
- test_prompt_validation.py: Tests prompt loading, content, and structure validation
- test_end_to_end.py: Tests complete agent workflows and user interactions
- test_langsmith_evaluations.py: Professional LLM/agent evaluations using LangSmith

Note: Only LangSmith evaluations are used for LLM/agent assessment to avoid misleading custom metrics.
"""

from .test_agent_creation import run_agent_creation_tests
from .test_tool_validation import run_tool_validation_tests
from .test_prompt_validation import run_prompt_validation_tests
from .test_end_to_end import run_end_to_end_tests
from .test_langsmith_evaluations import run_langsmith_evaluations


def run_all_underwriting_agent_tests():
    """
    Run all UnderwritingAgent test categories and return comprehensive results.
    
    Returns:
        dict: Comprehensive test results including:
            - total_tests: Total number of tests run
            - total_passed: Total number of tests passed
            - total_failed: Total number of tests failed
            - category_results: Detailed results by test category
            - overall_success_rate: Percentage of tests passed
    """
    print("🧪 RUNNING COMPREHENSIVE UNDERWRITING AGENT TEST SUITE")
    print("=" * 70)
    
    # Run all test categories
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
    
    for category_name, test_function in test_categories:
        print(f"\n📋 RUNNING {category_name.upper()} TESTS")
        print("-" * 50)
        
        try:
            category_results = test_function()
            comprehensive_results["category_results"][category_name] = category_results
            comprehensive_results["total_tests"] += category_results["total_tests"]
            comprehensive_results["total_passed"] += category_results["passed_tests"]
            comprehensive_results["total_failed"] += category_results["failed_tests"]
            
            print(f" {category_name}: {category_results['passed_tests']}/{category_results['total_tests']} passed")
            
        except Exception as e:
            print(f" {category_name}: Failed to run - {e}")
            comprehensive_results["category_results"][category_name] = {
                "total_tests": 1,
                "passed_tests": 0,
                "failed_tests": 1,
                "test_details": [f" Category failed to run: {e}"]
            }
            comprehensive_results["total_tests"] += 1
            comprehensive_results["total_failed"] += 1
    
    # Calculate overall success rate
    if comprehensive_results["total_tests"] > 0:
        comprehensive_results["overall_success_rate"] = (
            comprehensive_results["total_passed"] / comprehensive_results["total_tests"]
        ) * 100
    
    # Print comprehensive summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Tests Run: {comprehensive_results['total_tests']}")
    print(f"Total Passed: {comprehensive_results['total_passed']}")
    print(f"Total Failed: {comprehensive_results['total_failed']}")
    print(f"Overall Success Rate: {comprehensive_results['overall_success_rate']:.1f}%")
    
    print(f"\n📋 RESULTS BY CATEGORY:")
    for category_name, category_result in comprehensive_results["category_results"].items():
        success_rate = (category_result["passed_tests"] / category_result["total_tests"]) * 100 if category_result["total_tests"] > 0 else 0
        status = "" if category_result["failed_tests"] == 0 else ""
        print(f"{status} {category_name}: {category_result['passed_tests']}/{category_result['total_tests']} ({success_rate:.1f}%)")
    
    # Overall assessment
    if comprehensive_results["total_failed"] == 0:
        print("\n🎉 ALL UNDERWRITING AGENT TESTS PASSED!")
        print("🚀 UnderwritingAgent is production-ready!")
    else:
        print(f"\n⚠️ {comprehensive_results['total_failed']} TEST(S) FAILED")
        print("🔧 Please review and fix failing tests before production deployment.")
    
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
    "run_all_underwriting_agent_tests"
]
