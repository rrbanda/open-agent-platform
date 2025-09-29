"""
Test Individual Tool Validation

Tests for each of the 4 MortgageAdvisorAgent tools to ensure they work
correctly with Neo4j database and return expected responses.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.agents.mortgage_advisor_agent.tools import (
    explain_loan_programs,
    recommend_loan_program,
    check_qualification_requirements,
    guide_next_steps,
    validate_all_tools
)
from utils import initialize_connection


def test_explain_loan_programs_tool():
    """Test explain_loan_programs tool functionality."""
    print("🔧 Testing explain_loan_programs tool...")
    
    try:
        # Test with specific programs
        result1 = explain_loan_programs.invoke({
            "programs": "FHA,VA",
            "focus": "down payment"
        })
        
        # Validate response structure
        assert isinstance(result1, dict), "Result should be a dictionary"
        
        if "error" in result1:
            print(f"⚠️ Tool returned error: {result1['error']}")
            return False
        
        # Check for expected keys in successful response
        expected_keys = ["program_details", "comparison_summary"]
        for key in expected_keys:
            if key in result1:
                assert isinstance(result1[key], (dict, list)), f"{key} should be dict or list"
        
        # Test with single program
        result2 = explain_loan_programs.invoke({
            "programs": "VA"
        })
        
        assert isinstance(result2, dict), "Single program result should be a dictionary"
        
        print(" explain_loan_programs tool test passed")
        return True
        
    except Exception as e:
        print(f" explain_loan_programs tool failed: {e}")
        return False


def test_recommend_loan_program_tool():
    """Test recommend_loan_program tool functionality."""
    print("🔧 Testing recommend_loan_program tool...")
    
    try:
        # Test with veteran profile
        result = recommend_loan_program.invoke({
            "credit_score": 720,
            "down_payment_percent": 0.0,
            "dti_ratio": 0.25,
            "annual_income": 85000,
            "monthly_debts": 1500,
            "property_type": "primary_residence",
            "military_status": "veteran",
            "first_time_buyer": False,
            "property_location": "urban"
        })
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if not result.get("success", False):
            print(f"⚠️ Tool returned error: {result.get('error')}")
            return False
        
        # Check for expected keys in successful response
        required_keys = ["borrower_profile", "recommended_programs", "borrower_analysis"]
        for key in required_keys:
            assert key in result, f"Result should contain {key}"
            assert isinstance(result[key], (dict, list)), f"{key} should be dict or list"
        
        # Validate recommendations structure
        recommendations = result["recommended_programs"]
        assert isinstance(recommendations, list), "Recommendations should be a list"
        
        if recommendations:
            first_rec = recommendations[0]
            rec_keys = ["program_name", "qualification_status", "recommendation_score"]
            for key in rec_keys:
                assert key in first_rec, f"Recommendation should contain {key}"
        
        print(" recommend_loan_program tool test passed")
        return True
        
    except Exception as e:
        print(f" recommend_loan_program tool failed: {e}")
        return False


def test_check_qualification_requirements_tool():
    """Test check_qualification_requirements tool functionality."""
    print("🔧 Testing check_qualification_requirements tool...")
    
    try:
        # Test with VA loan analysis
        result = check_qualification_requirements.invoke({
            "loan_programs": "VA",
            "borrower_credit_score": 720,
            "borrower_down_payment": 0.0,
            "borrower_dti_ratio": 0.25,
            "military_status": "veteran",
            "property_location": "urban"
        })
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if not result.get("success", False):
            print(f"⚠️ Tool returned error: {result.get('error')}")
            return False
        
        # Check for expected keys
        required_keys = ["program_requirements", "qualification_gaps", "improvement_roadmap"]
        for key in required_keys:
            assert key in result, f"Result should contain {key}"
        
        # Validate program requirements structure
        program_reqs = result["program_requirements"]
        assert isinstance(program_reqs, list), "Program requirements should be a list"
        
        if program_reqs:
            first_prog = program_reqs[0]
            prog_keys = ["program_name", "basic_requirements", "overall_qualification"]
            for key in prog_keys:
                assert key in first_prog, f"Program requirement should contain {key}"
        
        print(" check_qualification_requirements tool test passed")
        return True
        
    except Exception as e:
        print(f" check_qualification_requirements tool failed: {e}")
        return False


def test_guide_next_steps_tool():
    """Test guide_next_steps tool functionality."""
    print("🔧 Testing guide_next_steps tool...")
    
    try:
        # Test with Application stage (one of the available stages)
        result = guide_next_steps.invoke({
            "current_stage": "Application",
            "selected_loan_program": "VA",
            "borrower_status": "first_time",
            "priority_focus": "timeline"
        })
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if not result.get("success", False):
            print(f"⚠️ Tool returned error: {result.get('error')}")
            # For guide_next_steps, we might have stage issues, so let's check available stages
            if "available_stages" in result:
                print(f"Available stages: {result['available_stages']}")
            return False
        
        # Check for expected keys
        required_keys = ["immediate_next_steps", "documentation_checklist", "timeline_expectations"]
        for key in required_keys:
            assert key in result, f"Result should contain {key}"
        
        # Validate immediate next steps structure
        next_steps = result["immediate_next_steps"]
        assert isinstance(next_steps, list), "Next steps should be a list"
        
        print(" guide_next_steps tool test passed")
        return True
        
    except Exception as e:
        print(f" guide_next_steps tool failed: {e}")
        return False


def test_tool_validation_functions():
    """Test the built-in tool validation functions."""
    print("🔧 Testing tool validation functions...")
    
    try:
        # Test the validate_all_tools function
        validation_results = validate_all_tools()
        
        assert isinstance(validation_results, dict), "Validation results should be a dictionary"
        
        # Check that all 4 tools are tested
        expected_tools = [
            "explain_loan_programs",
            "recommend_loan_program", 
            "check_qualification_requirements",
            "guide_next_steps"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in validation_results, f"Validation should include {tool_name}"
            # Each result should be a boolean
            assert isinstance(validation_results[tool_name], bool), f"{tool_name} validation should be boolean"
        
        # Report validation results
        passed_tools = sum(validation_results.values())
        total_tools = len(validation_results)
        print(f"   Built-in validation: {passed_tools}/{total_tools} tools passed")
        
        print(" Tool validation functions test passed")
        return True
        
    except Exception as e:
        print(f" Tool validation functions failed: {e}")
        return False


def test_neo4j_database_dependency():
    """Test that tools properly handle Neo4j database connection."""
    print("🔧 Testing Neo4j database dependency...")
    
    try:
        # Test database initialization
        connection_success = initialize_connection()
        
        if not connection_success:
            print("⚠️ Neo4j connection failed - tools may not work properly")
            return False
        
        # Test a simple tool call that requires database
        result = explain_loan_programs.invoke({
            "programs": "all"
        })
        
        # Should not return database connection errors
        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"].lower()
            if "neo4j" in error_msg or "database" in error_msg or "connection" in error_msg:
                print(f"⚠️ Database connection issue: {result['error']}")
                return False
        
        print(" Neo4j database dependency test passed")
        return True
        
    except Exception as e:
        print(f" Neo4j database dependency failed: {e}")
        return False


def run_tool_validation_tests():
    """Run all tool validation tests."""
    print("\n🧪 Running Tool Validation Tests")
    print("=" * 40)
    
    tests = [
        test_neo4j_database_dependency,  # Run this first
        test_explain_loan_programs_tool,
        test_recommend_loan_program_tool,
        test_check_qualification_requirements_tool,
        test_guide_next_steps_tool,
        test_tool_validation_functions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f" Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Tool Validation Tests: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    success = run_tool_validation_tests()
    sys.exit(0 if success else 1)
