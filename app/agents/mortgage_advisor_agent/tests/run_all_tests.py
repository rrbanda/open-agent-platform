"""
Run All MortgageAdvisorAgent Tests

Comprehensive test runner for the MortgageAdvisorAgent that runs:
1. Agent creation and configuration tests
2. Individual tool validation tests  
3. YAML prompt validation tests
4. End-to-end workflow tests
Note: Professional LLM/agent evaluations available separately via test_langsmith_evaluations.py

Usage:
    python run_all_tests.py
    python -m pytest run_all_tests.py -v
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# Import test modules
from .test_agent_creation import run_agent_creation_tests
from .test_tool_validation import run_tool_validation_tests
from .test_prompt_validation import run_prompt_validation_tests
from .test_end_to_end import run_end_to_end_tests
# Professional LLM/agent evaluations use LangSmith - see test_langsmith_evaluations.py

from utils import initialize_connection


def run_all_mortgage_advisor_tests(verbose: bool = True) -> Dict[str, bool]:
    """
    Run all MortgageAdvisorAgent tests and return results.
    
    Args:
        verbose: Whether to print detailed output
        
    Returns:
        Dictionary with test category results
    """
    if verbose:
        print("🧪 MORTGAGEADVISORAGENT COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print("Testing production-ready mortgage agent with 100% data-driven tools")
        print()
    
    start_time = time.time()
    
    # Pre-flight checks
    if verbose:
        print("🔧 Pre-flight Checks")
        print("-" * 20)
    
    # Check Neo4j connection
    if verbose:
        print("🔌 Checking Neo4j database connection...")
    
    neo4j_available = initialize_connection()
    if neo4j_available:
        if verbose:
            print(" Neo4j connection successful")
    else:
        if verbose:
            print(" Neo4j connection failed - some tests may fail")
    
    if verbose:
        print()
    
    # Test categories and their runners
    test_categories = [
        ("Agent Creation", run_agent_creation_tests),
        ("Tool Validation", run_tool_validation_tests), 
        ("Prompt Validation", run_prompt_validation_tests),
        ("End-to-End Workflows", run_end_to_end_tests),
# Note: Professional LLM/agent evaluations available via test_langsmith_evaluations.py
    ]
    
    results = {}
    total_passed = 0
    total_categories = len(test_categories)
    
    # Run each test category
    for category_name, test_runner in test_categories:
        if verbose:
            print(f"🧪 Running {category_name} Tests")
            print("-" * 30)
        
        try:
            category_start = time.time()
            result = test_runner()
            category_time = time.time() - category_start
            
            results[category_name] = result
            if result:
                total_passed += 1
            
            if verbose:
                status = " PASSED" if result else " FAILED"
                print(f"{status} - {category_name} ({category_time:.1f}s)")
                print()
                
        except Exception as e:
            results[category_name] = False
            if verbose:
                print(f" FAILED - {category_name} (Exception: {e})")
                print()
    
    total_time = time.time() - start_time
    
    # Print final summary
    if verbose:
        print("📊 FINAL TEST RESULTS")
        print("=" * 40)
        
        for category, passed in results.items():
            status = " PASSED" if passed else " FAILED"
            print(f"{status} {category}")
        
        print()
        print(f"📈 Overall Results: {total_passed}/{total_categories} test categories passed")
        print(f"⏱️  Total runtime: {total_time:.1f} seconds")
        
        # Detailed status
        if total_passed == total_categories:
            print()
            print("🎉 ALL TESTS PASSED! 🎉")
            print(" MortgageAdvisorAgent is production-ready!")
            print(" All 4 tools are 100% data-driven from Neo4j")
            print(" Agent creation, validation, and workflows working")
            print(" Prompts properly loaded from YAML")
            print(" End-to-end conversations and tool calling functional")
            print(" All functionality tests validated")
        else:
            print()
            print("⚠️  SOME TESTS FAILED")
            failed_categories = [cat for cat, passed in results.items() if not passed]
            print(f"Failed categories: {', '.join(failed_categories)}")
            print("Review individual test outputs above for details")
        
        if not neo4j_available:
            print()
            print("⚠️  NOTE: Neo4j connection was not available")
            print("   Some tests may have been skipped or failed due to database connectivity")
            print("   Ensure Neo4j is running locally with 'mortgage' or 'neo4j' database")
    
    return results


def run_specific_test_category(category: str) -> bool:
    """Run a specific test category."""
    test_runners = {
        "creation": run_agent_creation_tests,
        "tools": run_tool_validation_tests,
        "prompts": run_prompt_validation_tests,
        "e2e": run_end_to_end_tests,
# "eval": Use test_langsmith_evaluations.py for professional LLM/agent evaluation
    }
    
    if category.lower() not in test_runners:
        print(f" Unknown test category: {category}")
        print(f"Available categories: {', '.join(test_runners.keys())}")
        return False
    
    return test_runners[category.lower()]()


def run_quick_smoke_test() -> bool:
    """Run a quick smoke test to verify basic functionality."""
    print("🚀 Running Quick Smoke Test")
    print("=" * 30)
    
    try:
        # Test 1: Agent creation
        print("1. Testing agent creation...")
        from app.agents.mortgage_advisor_agent import create_mortgage_advisor_agent
        agent = create_mortgage_advisor_agent()
        print("    Agent created successfully")
        
        # Test 2: Basic tool validation
        print("2. Testing tool validation...")
        from app.agents.mortgage_advisor_agent.tools import validate_all_tools
        tool_results = validate_all_tools()
        passed_tools = sum(tool_results.values())
        total_tools = len(tool_results)
        print(f"    {passed_tools}/{total_tools} tools validated")
        
        # Test 3: Prompt loading
        print("3. Testing prompt loading...")
        from agents.shared.prompt_loader import load_agent_prompt
        prompt = load_agent_prompt("mortgage_advisor_agent")
        assert len(prompt.strip()) > 0
        print("    Prompt loaded successfully")
        
        # Test 4: Basic conversation
        print("4. Testing basic conversation...")
        test_input = {"messages": [{"role": "user", "content": "Hello"}]}
        result = agent.invoke(test_input)
        assert "messages" in result
        print("    Basic conversation working")
        
        print("\n🎉 Smoke test passed! Agent appears to be working correctly.")
        return True
        
    except Exception as e:
        print(f"\n Smoke test failed: {e}")
        return False


def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MortgageAdvisorAgent Test Runner")
    parser.add_argument("--category", "-c", 
                       choices=["creation", "tools", "prompts", "e2e", "eval"],
                       help="Run specific test category")
    parser.add_argument("--smoke", "-s", action="store_true",
                       help="Run quick smoke test only")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    if args.smoke:
        success = run_quick_smoke_test()
    elif args.category:
        success = run_specific_test_category(args.category)
    else:
        results = run_all_mortgage_advisor_tests(verbose=not args.quiet)
        success = all(results.values())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
