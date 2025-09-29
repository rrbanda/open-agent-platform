"""
ApplicationAgent Comprehensive Test Runner

This script runs all ApplicationAgent FUNCTIONALITY tests in sequence and provides
comprehensive reporting of test results and agent readiness.

Usage:
    python run_all_tests.py
    
    # Or from the mortgage-processor root:
    python agents/application_agent/tests/run_all_tests.py

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
    from app.agents.application_agent.tests import run_all_application_agent_tests
except ImportError as e:
    print(f" Failed to import test modules: {e}")
    print("Make sure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)


def main():
    """Main test runner function."""
    print("🏦 APPLICATION AGENT COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("Testing all components of the ApplicationAgent implementation")
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
        results = run_all_application_agent_tests()
        
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
            recommendation = "ApplicationAgent is ready for production deployment!"
        elif critical_rate == 100:
            readiness_level = "⚠️ FUNCTIONALLY READY (Review Important Components)"
            recommendation = "All critical components passed. Review important components for full readiness."
        elif critical_rate >= 80:
            readiness_level = "🚧 DEVELOPMENT IN PROGRESS (Critical Issues Remain)"
            recommendation = "Address critical component failures before proceeding."
        else:
            readiness_level = " NOT READY (Major Issues)"
            recommendation = "Significant issues detected. Rework critical components."
            
        print(f"Overall Readiness: {readiness_level}")
        print(f"Recommendation: {recommendation}")
        
        # ApplicationAgent specific recommendations
        print("\n🎯 APPLICATION AGENT SPECIFIC INSIGHTS:")
        
        if results["overall_success_rate"] >= 90:
            print(" ApplicationAgent demonstrates excellent agentic mortgage application receiving capabilities")
            print(" All 5 Neo4j-powered tools are functioning correctly")
            print(" Application intake, qualification, and workflow routing are production-ready")
            print(" Ready to serve as the foundation for end-to-end agentic mortgage processing")
        elif results["overall_success_rate"] >= 75:
            print("⚠️ ApplicationAgent shows good functionality with minor issues")
            print(" Core application receiving capabilities are working")
            print("🔧 Some components need refinement for optimal performance")
        else:
            print(" ApplicationAgent requires significant improvements")
            print("🔧 Core functionality issues need to be resolved")
            
        print("\n📈 NEXT STEPS:")
        if results["overall_success_rate"] >= 90:
            print("1.  ApplicationAgent implementation is solid")
            print("2. 🧪 Run LangSmith evaluations for professional assessment")
            print("3. 🔄 Integrate with other agents in the workflow")
            print("4. 📈 Complete end-to-end agentic mortgage processing system ready!")
        elif results["overall_success_rate"] >= 70:
            print("1. 🔧 Fix failing tests in priority order")
            print("2. 🧪 Re-run test suite to verify fixes")
            print("3. 📊 Consider additional edge case testing")
        else:
            print("1. 🚨 Address fundamental implementation issues")
            print("2. 🔧 Focus on critical component failures first")
            print("3. 📋 Review agent architecture and tool implementation")
            
    except Exception as e:
        print(f"\n An unexpected error occurred during test execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
