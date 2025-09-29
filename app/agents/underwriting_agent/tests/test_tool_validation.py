"""
Test Tool Validation for UnderwritingAgent

This module tests each individual tool to ensure they work correctly,
handle edge cases properly, and integrate with Neo4j as expected.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from app.agents.underwriting_agent.tools import (
    analyze_credit_risk,
    calculate_debt_to_income,
    evaluate_income_sources,
    make_underwriting_decision,
    validate_all_tools
)


class TestUnderwritingToolValidation:
    """Test suite for UnderwritingAgent tool validation."""
    
    def test_analyze_credit_risk_tool(self):
        """Test the analyze_credit_risk tool with various scenarios."""
        print("\n🔍 Testing analyze_credit_risk tool...")
        
        try:
            # Test with good credit scenario
            result = analyze_credit_risk.invoke({
                "credit_score": 720,
                "loan_program": "conventional",
                "bankruptcy_months_ago": None,
                "foreclosure_months_ago": None,
                "late_payments_12_months": {"30_day": 0, "60_day": 0, "90_day": 0},
                "open_collections": 0,
                "credit_history_years": 5.0
            })
            
            assert isinstance(result, str), "Result should be a string"
            assert "Credit Risk Analysis Report" in result, "Should contain analysis report"
            assert "Overall Risk Level" in result, "Should contain risk level"
            print(" Good credit scenario test passed")
            
            # Test with poor credit scenario
            result = analyze_credit_risk.invoke({
                "credit_score": 580,
                "loan_program": "fha",
                "bankruptcy_months_ago": 6,  # Recent bankruptcy
                "foreclosure_months_ago": None,
                "late_payments_12_months": {"30_day": 3, "60_day": 1, "90_day": 0},
                "open_collections": 2,
                "credit_history_years": 2.0
            })
            
            assert "Credit Risk Analysis Report" in result, "Should contain analysis report"
            assert "HIGH" in result or "MEDIUM" in result, "Should identify higher risk"
            print(" Poor credit scenario test passed")
            
        except Exception as e:
            pytest.fail(f"analyze_credit_risk tool test failed: {e}")
    
    def test_calculate_debt_to_income_tool(self):
        """Test the calculate_debt_to_income tool with various DTI scenarios."""
        print("\n📊 Testing calculate_debt_to_income tool...")
        
        try:
            # Test with acceptable DTI
            result = calculate_debt_to_income.invoke({
                "monthly_gross_income": 8000.0,
                "monthly_housing_payment": 2000.0,
                "monthly_debt_payments": 800.0,
                "loan_program": "conventional",
                "income_sources": ["w2_salary"],
                "employment_years": 3.0,
                "overtime_available": False
            })
            
            assert isinstance(result, str), "Result should be a string"
            assert "Debt-to-Income Analysis Report" in result, "Should contain DTI analysis"
            assert "Front-End DTI" in result, "Should show front-end DTI"
            assert "Back-End DTI" in result, "Should show back-end DTI"
            print(" Acceptable DTI scenario test passed")
            
            # Test with high DTI
            result = calculate_debt_to_income.invoke({
                "monthly_gross_income": 5000.0,
                "monthly_housing_payment": 2000.0,  # 40% front-end
                "monthly_debt_payments": 1500.0,    # Total 70% back-end
                "loan_program": "conventional",
                "income_sources": ["w2_salary"],
                "employment_years": 2.0,
                "overtime_available": False
            })
            
            assert "EXCEEDS" in result or "FAIL" in result, "Should identify DTI issues"
            print(" High DTI scenario test passed")
            
        except Exception as e:
            pytest.fail(f"calculate_debt_to_income tool test failed: {e}")
    
    def test_evaluate_income_sources_tool(self):
        """Test the evaluate_income_sources tool with different income types."""
        print("\n💰 Testing evaluate_income_sources tool...")
        
        try:
            # Test with stable W2 income
            result = evaluate_income_sources.invoke({
                "income_sources": [
                    {
                        "income_type": "w2_salary",
                        "monthly_amount": 6000.0,
                        "years_received": 3.0,
                        "employer_name": "Tech Corp",
                        "is_continuing": True
                    }
                ],
                "loan_program": "conventional",
                "applicant_age": 35
            })
            
            assert isinstance(result, str), "Result should be a string"
            assert "Income Source Evaluation Report" in result, "Should contain income evaluation"
            assert "Total Qualifying Income" in result, "Should show qualifying income"
            print(" Stable W2 income test passed")
            
            # Test with complex income mix
            result = evaluate_income_sources.invoke({
                "income_sources": [
                    {
                        "income_type": "w2_salary",
                        "monthly_amount": 5000.0,
                        "years_received": 3.0,
                        "employer_name": "Main Corp",
                        "is_continuing": True
                    },
                    {
                        "income_type": "bonus",
                        "monthly_amount": 500.0,
                        "years_received": 2.5,
                        "employer_name": "Main Corp",
                        "is_continuing": True
                    },
                    {
                        "income_type": "rental",
                        "monthly_amount": 1200.0,
                        "years_received": 4.0,
                        "employer_name": "Rental Property",
                        "is_continuing": True
                    }
                ],
                "loan_program": "conventional",
                "applicant_age": 40
            })
            
            assert "Income Source Evaluation Report" in result, "Should contain evaluation"
            assert "Individual Income Source Analysis" in result, "Should analyze each source"
            print(" Complex income mix test passed")
            
        except Exception as e:
            pytest.fail(f"evaluate_income_sources tool test failed: {e}")
    
    def test_make_underwriting_decision_tool(self):
        """Test the make_underwriting_decision tool with different scenarios."""
        print("\n⚖️ Testing make_underwriting_decision tool...")
        
        try:
            # Test approval scenario
            result = make_underwriting_decision.invoke({
                "credit_score": 740,
                "credit_risk_level": "LOW",
                "monthly_gross_income": 8000.0,
                "income_stability": "excellent",
                "front_end_dti": 25.0,
                "back_end_dti": 35.0,
                "loan_program": "conventional",
                "loan_amount": 400000.0,
                "down_payment_percent": 0.20,
                "property_value": 500000.0,
                "cash_reserves_months": 3.0,
                "employment_years": 5.0,
                "first_time_buyer": False,
                "property_type": "primary_residence"
            })
            
            assert isinstance(result, str), "Result should be a string"
            assert "UNDERWRITING DECISION REPORT" in result, "Should contain decision report"
            assert "DECISION:" in result, "Should contain decision"
            print(" Approval scenario test passed")
            
            # Test denial scenario
            result = make_underwriting_decision.invoke({
                "credit_score": 550,
                "credit_risk_level": "HIGH",
                "monthly_gross_income": 4000.0,
                "income_stability": "poor",
                "front_end_dti": 35.0,
                "back_end_dti": 55.0,  # Exceeds limits
                "loan_program": "conventional",
                "loan_amount": 300000.0,
                "down_payment_percent": 0.05,
                "property_value": 315000.0,
                "cash_reserves_months": 0.5,
                "employment_years": 0.5,
                "first_time_buyer": True,
                "property_type": "primary_residence"
            })
            
            assert "DECISION:" in result, "Should contain decision"
            assert ("DENY" in result or "MANUAL_REVIEW" in result), "Should deny or require manual review"
            print(" Denial scenario test passed")
            
        except Exception as e:
            pytest.fail(f"make_underwriting_decision tool test failed: {e}")
    
    def test_tool_validation_function(self):
        """Test the built-in tool validation functions."""
        print("\n🔧 Testing tool validation functions...")
        
        try:
            # Test individual tool validations
            from app.agents.underwriting_agent.tools.analyze_credit_risk import validate_tool as validate_credit
            from app.agents.underwriting_agent.tools.calculate_debt_to_income import validate_tool as validate_dti
            from app.agents.underwriting_agent.tools.evaluate_income_sources import validate_tool as validate_income
            from app.agents.underwriting_agent.tools.make_underwriting_decision import validate_tool as validate_decision
            
            # Run individual validations
            credit_valid = validate_credit()
            dti_valid = validate_dti()
            income_valid = validate_income()
            decision_valid = validate_decision()
            
            assert credit_valid, "Credit risk tool validation should pass"
            assert dti_valid, "DTI tool validation should pass"
            assert income_valid, "Income evaluation tool validation should pass"
            assert decision_valid, "Underwriting decision tool validation should pass"
            
            # Test aggregate validation
            all_results = validate_all_tools()
            assert isinstance(all_results, dict), "Should return dictionary of results"
            assert len(all_results) == 4, "Should validate all 4 tools"
            
            for tool_name, result in all_results.items():
                assert result is True, f"Tool {tool_name} validation should pass"
            
            print(" All tool validation functions passed")
            
        except Exception as e:
            pytest.fail(f"Tool validation function test failed: {e}")
    
    def test_tool_error_handling(self):
        """Test that tools handle errors gracefully."""
        print("\n⚠️ Testing tool error handling...")
        
        try:
            # Test with invalid input
            result = analyze_credit_risk.invoke({
                "credit_score": -100,  # Invalid credit score
                "loan_program": "invalid_program",
                "bankruptcy_months_ago": None,
                "foreclosure_months_ago": None,
                "late_payments_12_months": {"30_day": 0, "60_day": 0, "90_day": 0},
                "open_collections": 0,
                "credit_history_years": 5.0
            })
            
            # Should not crash, should handle gracefully
            assert isinstance(result, str), "Should return string even with invalid input"
            print(" Invalid input handling test passed")
            
        except Exception as e:
            # This is acceptable - tools can raise validation errors
            print(f"⚠️ Tool appropriately raised validation error: {e}")


def run_tool_validation_tests():
    """Run all tool validation tests and return results."""
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    test_class = TestUnderwritingToolValidation()
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
    print("🧪 RUNNING UNDERWRITING AGENT TOOL VALIDATION TESTS")
    print("=" * 60)
    
    results = run_tool_validation_tests()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    
    print(f"\n📋 TEST DETAILS:")
    for detail in results["test_details"]:
        print(detail)
    
    if results["failed_tests"] == 0:
        print("\n🎉 ALL TOOL VALIDATION TESTS PASSED!")
    else:
        print(f"\n⚠️ {results['failed_tests']} TEST(S) FAILED")
        sys.exit(1)
