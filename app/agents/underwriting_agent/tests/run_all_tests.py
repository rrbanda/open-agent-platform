"""
UnderwritingAgent Test Runner

This script runs all UnderwritingAgent FUNCTIONALITY tests in sequence and provides
comprehensive reporting of test results and agent readiness.

Usage:
    python run_all_tests.py
    
    # Or from the mortgage-processor root:
    python agents/underwriting_agent/tests/run_all_tests.py

Features:
- Runs all FUNCTIONALITY test categories in logical order
- Provides detailed progress reporting
- Summarizes results with actionable recommendations
- Determines production readiness based on test results

Note: For LLM/agent evaluations, use test_langsmith_evaluations.py separately.
Only LangSmith evaluations are used for LLM/agent assessment to avoid misleading metrics.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

# Import test runners
try:
    from app.agents.underwriting_agent.tests import run_all_underwriting_agent_tests
except ImportError as e:
    print(f" Failed to import test modules: {e}")
    print("Make sure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)


def main():
    """Main test runner function."""
    print("🏦 UNDERWRITING AGENT COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("Testing all components of the UnderwritingAgent implementation")
    print("following the established testing patterns from other agents.")
    print()
    
    # Environment check
    print("🔍 ENVIRONMENT CHECK:")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Test script location: {current_dir}")
    print(f"Source directory: {src_dir}")
    
    # Check if Neo4j environment is set up
    neo4j_password = os.environ.get('NEO4J_PASSWORD')
    if neo4j_password:
        print(" Neo4j password environment variable found")
    else:
        print("⚠️ Neo4j password environment variable not found")
        print("   Set NEO4J_PASSWORD environment variable for database tests")
    
    print()
    
    # Run comprehensive tests
    try:
        results = run_all_underwriting_agent_tests()
        
        # Detailed analysis and recommendations
        print("\n" + "=" * 70)
        print("📋 DETAILED ANALYSIS AND RECOMMENDATIONS")
        print("=" * 70)
        
        # Analyze results by category
        critical_categories = ["Agent Creation", "Tool Validation"]
        important_categories = ["Prompt Validation", "End-to-End"]
        
        critical_passed = sum(
            results["category_results"].get(cat, {}).get("passed_tests", 0) 
            for cat in critical_categories
        )
        critical_total = sum(
            results["category_results"].get(cat, {}).get("total_tests", 0) 
            for cat in critical_categories
        )
        
        important_passed = sum(
            results["category_results"].get(cat, {}).get("passed_tests", 0) 
            for cat in important_categories
        )
        important_total = sum(
            results["category_results"].get(cat, {}).get("total_tests", 0) 
            for cat in important_categories
        )
        
        
        # Production readiness assessment
        print("🎯 PRODUCTION READINESS ASSESSMENT:")
        
        critical_rate = (critical_passed / critical_total * 100) if critical_total > 0 else 0
        important_rate = (important_passed / important_total * 100) if important_total > 0 else 0
        
        print(f"Critical Components: {critical_passed}/{critical_total} ({critical_rate:.1f}%)")
        print(f"Important Components: {important_passed}/{important_total} ({important_rate:.1f}%)")
        
        # Determine readiness level
        if critical_rate == 100 and important_rate >= 80:
            readiness_level = "🚀 PRODUCTION READY"
            recommendation = "UnderwritingAgent is ready for production deployment!"
        elif critical_rate >= 90 and important_rate >= 70:
            readiness_level = "⚠️ NEARLY READY"
            recommendation = "Address remaining issues before production deployment."
        elif critical_rate >= 70:
            readiness_level = "🔧 NEEDS WORK"
            recommendation = "Significant issues need to be resolved before deployment."
        else:
            readiness_level = " NOT READY"
            recommendation = "Major issues prevent production deployment."
        
        print(f"\n📊 OVERALL READINESS: {readiness_level}")
        print(f"💡 RECOMMENDATION: {recommendation}")
        
        # Specific recommendations
        print(f"\n🔧 SPECIFIC RECOMMENDATIONS:")
        
        failed_categories = [
            cat for cat, result in results["category_results"].items() 
            if result["failed_tests"] > 0
        ]
        
        if not failed_categories:
            print(" All test categories passed - excellent work!")
            print(" Agent is following established patterns correctly")
            print(" Ready to proceed with integration testing")
        else:
            print("⚠️ Failed test categories need attention:")
            for cat in failed_categories:
                failed_count = results["category_results"][cat]["failed_tests"]
                print(f"   • {cat}: {failed_count} failed test(s)")
        
        # Next steps
        print(f"\n📋 NEXT STEPS:")
        if results["overall_success_rate"] >= 90:
            print("1.  UnderwritingAgent implementation is solid")
            print("2. 🔄 Proceed with integration into main workflow")
            print("3. 🧪 Set up UI testing with LangGraph Studio")
            print("4. 📈 All agents completed - system ready for production")
        elif results["overall_success_rate"] >= 70:
            print("1. 🔧 Fix failing tests in priority order")
            print("2. 🧪 Re-run test suite to verify fixes")
            print("3. 📊 Consider additional edge case testing")
        else:
            print("1.  Review implementation against working templates")
            print("2. 🔧 Address fundamental issues first")
            print("3. 🧪 Focus on critical component tests")
        
        # Exit with appropriate code
        if results["total_failed"] == 0:
            print(f"\n🎉 SUCCESS: All {results['total_tests']} tests passed!")
            sys.exit(0)
        else:
            print(f"\n FAILURE: {results['total_failed']} of {results['total_tests']} tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n CRITICAL ERROR: Test suite failed to run")
        print(f"Error details: {e}")
        print("\nPlease check:")
        print("1. All dependencies are installed")
        print("2. Neo4j is running and accessible") 
        print("3. Environment variables are set correctly")
        print("4. File paths and imports are correct")
        sys.exit(1)


if __name__ == "__main__":
    main()
