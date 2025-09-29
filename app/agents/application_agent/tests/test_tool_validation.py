"""
ApplicationAgent Tool Validation Tests

This module tests all 5 ApplicationAgent tools individually to ensure they work correctly
with various input scenarios and handle edge cases appropriately.

Tools tested:
- receive_mortgage_application: Application intake and validation
- check_application_completeness: Completeness verification  
- perform_initial_qualification: Initial qualification assessment
- track_application_status: Application status tracking
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

try:
    from app.agents.application_agent.tools import (
        receive_mortgage_application,
        check_application_completeness,
        perform_initial_qualification,
        track_application_status,
        validate_all_tools
    )
    from utils import initialize_connection
    from app.utils.db.rules.application_intake import load_application_intake_rules
    from utils import get_neo4j_connection
    
    print("🔧 Testing ApplicationAgent Tools...")
    
    # Initialize connections and load rules
    initialize_connection()
    connection = get_neo4j_connection()
    load_application_intake_rules(connection)
    print(" Database initialized and rules loaded")
    
    # Test 1: Individual tool validation using built-in validators
    print("\n1. Testing individual tool validators...")
    tool_results = validate_all_tools()
    for tool_name, result in tool_results.items():
        status = " PASS" if result else " FAIL"
        print(f"   {status}: {tool_name}")
    
    all_tools_pass = all(tool_results.values())
    assert all_tools_pass, f"Not all tools passed validation: {tool_results}"
    print("    All tools pass their individual validators")
    
    # Test 2: Detailed application intake tool test
    print("\n2. Testing receive_mortgage_application with detailed scenario...")
    application_result = receive_mortgage_application.invoke({
        "first_name": "Jane",
        "last_name": "Doe", 
        "ssn": "123-45-6789",
        "date_of_birth": "1985-06-15",
        "phone": "555-987-6543",
        "email": "jane.doe@email.com",
        "current_street": "456 Oak Street",
        "current_city": "San Francisco",
        "current_state": "CA",
        "current_zip": "94102",
        "years_at_address": 2.5,
        "employer_name": "TechCorp",
        "job_title": "Product Manager",
        "years_employed": 3.5,
        "monthly_gross_income": 9500.0,
        "employment_type": "w2",
        "loan_purpose": "purchase",
        "loan_amount": 500000.0,
        "property_address": "789 Elm Ave, San Francisco, CA 94102",
        "property_value": 625000.0,
        "property_type": "condominium",
        "occupancy_type": "primary_residence",
        "credit_score": 750,
        "monthly_debts": 1800.0,
        "liquid_assets": 150000.0,
        "down_payment": 125000.0,
        "first_time_buyer": True,
        "military_service": False,
        "rural_property": False
    })
    
    assert "MORTGAGE APPLICATION INTAKE REPORT" in application_result
    assert "APPLICATION STATUS" in application_result
    assert "Jane" in application_result and "Doe" in application_result
    print("    Application intake working with detailed data")
    
    # Test 3: Application completeness check
    print("\n3. Testing check_application_completeness...")
    completeness_result = check_application_completeness.invoke({
        "application_id": "APP_20240101_123456_DOE",
        "loan_purpose": "purchase",
        "employment_type": "w2",
        "has_co_borrower": False,
        "property_type": "condominium",
        "occupancy_type": "primary_residence",
        "personal_info_complete": True,
        "address_info_complete": True,
        "employment_info_complete": True,
        "income_documentation": True,
        "asset_documentation": True,
        "debt_documentation": False,
        "property_documentation": True,
        "insurance_documentation": False,
        "tax_returns_provided": False,
        "bank_statements_provided": True,
        "paystubs_provided": True,
        "w2_forms_provided": True,
        "credit_report_authorized": True
    })
    
    assert "APPLICATION COMPLETENESS ANALYSIS" in completeness_result
    assert "STATUS ASSESSMENT" in completeness_result
    print("    Application completeness check working")
    
    # Test 4: Initial qualification test
    print("\n4. Testing perform_initial_qualification...")
    qualification_result = perform_initial_qualification.invoke({
        "application_id": "APP_20240101_123456_DOE",
        "credit_score": 750,
        "monthly_gross_income": 9500.0,
        "monthly_debts": 1800.0,
        "liquid_assets": 150000.0,
        "employment_years": 3.5,
        "employment_type": "w2",
        "loan_amount": 500000.0,
        "property_value": 625000.0,
        "down_payment": 125000.0,
        "property_type": "condominium",
        "occupancy_type": "primary_residence",
        "loan_purpose": "purchase",
        "first_time_buyer": True,
        "military_service": False,
        "rural_property": False,
        "bankruptcy_history": False,
        "foreclosure_history": False,
        "collections_amount": 0,
        "late_payments_12_months": 0
    })
    
    assert "INITIAL QUALIFICATION ASSESSMENT" in qualification_result
    assert "OVERALL ASSESSMENT" in qualification_result
    print("    Initial qualification assessment working")
    
    # Test 5: Application status tracking test
    print("\n5. Testing track_application_status...")
    status_result = track_application_status.invoke({
        "application_id": "APP_20240101_123456_DOE",
        "current_status": "in_processing",
        "requested_action": "check_status"
    })
    
    assert "APPLICATION STATUS TRACKING" in status_result
    assert "STATUS ANALYSIS" in status_result
    print("    Application status tracking working")
    
    # Test 7: Edge case handling - incomplete data
    print("\n7. Testing edge cases...")
    
    # Test with minimal data
    minimal_application = receive_mortgage_application.invoke({
        "first_name": "Test",
        "last_name": "User",
        "ssn": "000-00-0000",  # Invalid format
        "date_of_birth": "1990-01-01",
        "phone": "555-0000",  # Invalid format
        "email": "test@test.com",
        "current_street": "123 Test St",
        "current_city": "Test City",
        "current_state": "CA",
        "current_zip": "90210",
        "years_at_address": 1.0,
        "employer_name": "Test Corp",
        "job_title": "Tester",
        "years_employed": 1.0,
        "monthly_gross_income": 5000.0,
        "employment_type": "w2",
        "loan_purpose": "purchase",
        "loan_amount": 300000.0,
        "property_address": "456 Test Ave",
        "property_type": "single_family_detached",
        "occupancy_type": "primary_residence"
    })
    
    assert "VALIDATION ISSUES" in minimal_application or "VALIDATION WARNINGS" in minimal_application
    print("    Edge case handling working (validation issues detected)")
    
    print("\n🎉 All tool validation tests passed!")
    
except Exception as e:
    print(f"\n Tool validation test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def run_tool_validation_tests():
    """
    Run ApplicationAgent tool validation tests and return success status.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        # Initialize database and load rules
        initialize_connection()
        connection = get_neo4j_connection()
        load_application_intake_rules(connection)
        
        # Run all tool validators
        tool_results = validate_all_tools()
        all_pass = all(tool_results.values())
        
        if not all_pass:
            print(f"Tool validation failed: {tool_results}")
            return False
        
        # Test one complex scenario
        application_result = receive_mortgage_application.invoke({
            "first_name": "Test",
            "last_name": "User",
            "ssn": "123-45-6789",
            "date_of_birth": "1990-01-01",
            "phone": "555-123-4567",
            "email": "test@email.com",
            "current_street": "123 Test St",
            "current_city": "Test City",
            "current_state": "CA",
            "current_zip": "90210",
            "years_at_address": 2.0,
            "employer_name": "Test Corp",
            "job_title": "Tester",
            "years_employed": 3.0,
            "monthly_gross_income": 7000.0,
            "employment_type": "w2",
            "loan_purpose": "purchase",
            "loan_amount": 350000.0,
            "property_address": "456 Test Ave",
            "property_value": 400000.0,
            "property_type": "single_family_detached",
            "occupancy_type": "primary_residence",
            "credit_score": 700,
            "monthly_debts": 1000.0,
            "liquid_assets": 80000.0,
            "down_payment": 50000.0
        })
        
        return "MORTGAGE APPLICATION INTAKE REPORT" in application_result
        
    except Exception as e:
        print(f"Tool validation test error: {e}")
        return False


if __name__ == "__main__":
    # When run directly, execute the tests
    pass
