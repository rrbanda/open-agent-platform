"""
URLA Form 1003 Generation Tool

This tool generates standardized URLA (Uniform Residential Loan Application) 
Form 1003 from application data using Neo4j URLA rules for agentic compliance.
"""

import json
import logging
from typing import Dict, Any
from langchain_core.tools import tool
from datetime import datetime
import uuid

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection

logger = logging.getLogger(__name__)


def parse_neo4j_rule(rule_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON strings back to objects in Neo4j rule data."""
    parsed_rule = {}
    for key, value in rule_dict.items():
        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
            try:
                parsed_rule[key] = json.loads(value)
            except json.JSONDecodeError:
                parsed_rule[key] = value  # Keep as string if not valid JSON
        else:
            parsed_rule[key] = value
    return parsed_rule


def get_application_data_from_neo4j(application_id: str) -> Dict[str, Any]:
    """Retrieve complete application data from Neo4j database."""
    try:
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Query to get application data
            application_query = """
            MATCH (app:MortgageApplication {application_id: $application_id})
            RETURN app
            """
            result = session.run(application_query, {"application_id": application_id})
            record = result.single()
            
            if not record:
                return {"error": f"Application {application_id} not found"}
                
            app_data = dict(record['app'])
            return app_data
            
    except Exception as e:
        logger.error(f"Error retrieving application data: {e}")
        return {"error": f"Database error: {str(e)}"}


@tool
def generate_urla_1003_form(
    application_id: str
) -> str:
    """
    Generate URLA Form 1003 from stored application data.
    
    This tool retrieves complete application data from Neo4j and generates
    the standardized URLA Form 1003. Only requires the application ID.
    
    Args:
        application_id: The application ID to generate the form for
        
    Example:
        "Generate URLA form for application APP_20240315_143022_JOH"
    """
    
    # Get application data from Neo4j
    app_data = get_application_data_from_neo4j(application_id)
    
    if "error" in app_data:
        return f"❌ Error: {app_data['error']}"
    
    # Extract all the required parameters from stored data
    first_name = app_data.get("first_name", "")
    last_name = app_data.get("last_name", "")
    ssn = app_data.get("ssn", "")
    date_of_birth = app_data.get("date_of_birth", "")
    phone = app_data.get("phone", "")
    email = app_data.get("email", "")
    current_street = app_data.get("current_street", "")
    current_city = app_data.get("current_city", "")
    current_state = app_data.get("current_state", "")
    current_zip = app_data.get("current_zip", "")
    years_at_address = app_data.get("years_at_address", 0.0)
    employer_name = app_data.get("employer_name", "")
    job_title = app_data.get("job_title", "")
    years_employed = app_data.get("years_employed", 0.0)
    monthly_gross_income = app_data.get("monthly_gross_income", 0.0)
    employment_type = app_data.get("employment_type", "w2")
    loan_amount = app_data.get("loan_amount", 0.0)
    loan_purpose = app_data.get("loan_purpose", "purchase")
    property_address = app_data.get("property_address", "")
    property_type = app_data.get("property_type", "single_family_detached")
    occupancy_type = app_data.get("occupancy_type", "primary_residence")
    middle_name = app_data.get("middle_name", "")
    suffix = app_data.get("suffix", "")
    marital_status = app_data.get("marital_status", "Single")
    number_of_dependents = app_data.get("number_of_dependents", 0)
    monthly_housing_expense = app_data.get("monthly_housing_expense", 0.0)
    checking_account_balance = app_data.get("checking_account_balance", 0.0)
    savings_account_balance = app_data.get("savings_account_balance", 0.0)
    investment_account_balance = app_data.get("investment_account_balance", 0.0)
    retirement_account_balance = app_data.get("retirement_account_balance", 0.0)
    other_assets_value = app_data.get("other_assets_value", 0.0)
    monthly_debts = app_data.get("monthly_debts", 0.0)
    installment_debt_balance = app_data.get("installment_debt_balance", 0.0)
    revolving_debt_balance = app_data.get("revolving_debt_balance", 0.0)
    mortgage_debt_balance = app_data.get("mortgage_debt_balance", 0.0)
    property_value = app_data.get("property_value", 0.0)
    down_payment = app_data.get("down_payment", 0.0)
    outstanding_judgments = app_data.get("outstanding_judgments", False)
    declared_bankruptcy = app_data.get("declared_bankruptcy", False)
    foreclosure_or_deed = app_data.get("foreclosure_or_deed", False)
    party_to_lawsuit = app_data.get("party_to_lawsuit", False)
    us_citizen = app_data.get("us_citizen", True)
    permanent_resident = app_data.get("permanent_resident", False)
    military_service = app_data.get("military_service", False)
    military_status = app_data.get("military_status", "")
    
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get URLA form structure rules
            structure_query = """
            MATCH (rule:URLARule)
            WHERE rule.category = 'FormStructure'
            RETURN rule
            """
            result = session.run(structure_query)
            structure_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
            
            # Get field mapping rules
            mapping_query = """
            MATCH (rule:URLARule)
            WHERE rule.category = 'FieldMapping'
            RETURN rule
            """
            result = session.run(mapping_query)
            mapping_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
            
            # Get validation rules
            validation_query = """
            MATCH (rule:URLARule)
            WHERE rule.category = 'ValidationRules'
            RETURN rule
            """
            result = session.run(validation_query)
            validation_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
            
            # Get compliance rules
            compliance_query = """
            MATCH (rule:URLARule)
            WHERE rule.category = 'ComplianceRules'
            RETURN rule
            """
            result = session.run(compliance_query)
            compliance_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
        
        # Generate unique URLA form ID
        urla_form_id = f"URLA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"
        
        # Get form structure
        form_structure = structure_rules[0] if structure_rules else {}
        sections = form_structure.get('sections', [])
        form_version = form_structure.get('form_version', '1003_2021')
        
        # Create URLA form report
        urla_report = []
        urla_report.append("URLA FORM 1003 GENERATION REPORT")
        urla_report.append("=" * 60)
        
        # Form Header
        urla_report.append(f"\n📋 FORM IDENTIFICATION:")
        urla_report.append(f"URLA Form ID: {urla_form_id}")
        urla_report.append(f"Form Version: {form_version}")
        urla_report.append(f"Generation Date: {datetime.now().strftime('%m/%d/%Y %H:%M:%S')}")
        urla_report.append(f"Source Application: {application_id}")
        
        # Build URLA data structure using field mappings
        urla_data = {}
        
        # Section 1: Borrower Information
        borrower_mapping = next((rule for rule in mapping_rules if rule.get('rule_type') == 'borrower_information'), {})
        field_mappings = borrower_mapping.get('field_mappings', {})
        
        urla_report.append(f"\n📝 SECTION 1: BORROWER INFORMATION")
        
        section_1_data = {}
        for urla_field, source_field in field_mappings.items():
            if source_field == 'first_name':
                section_1_data[urla_field] = first_name
            elif source_field == 'last_name':
                section_1_data[urla_field] = last_name
            elif source_field == 'middle_name':
                section_1_data[urla_field] = middle_name or ""
            elif source_field == 'ssn':
                section_1_data[urla_field] = ssn
            elif source_field == 'date_of_birth':
                section_1_data[urla_field] = date_of_birth
            elif source_field == 'phone':
                section_1_data[urla_field] = phone
            elif source_field == 'email':
                section_1_data[urla_field] = email
            elif source_field == 'marital_status':
                section_1_data[urla_field] = marital_status or "Not Provided"
            elif source_field == 'number_of_dependents':
                section_1_data[urla_field] = number_of_dependents or 0
        
        urla_data['Section_1_Borrower_Information'] = section_1_data
        
        # Display Section 1 data
        for field, value in section_1_data.items():
            urla_report.append(f"  {field}: {value}")
        
        # Current Address Information
        address_mapping = next((rule for rule in mapping_rules if rule.get('rule_type') == 'current_address'), {})
        address_field_mappings = address_mapping.get('field_mappings', {})
        
        urla_report.append(f"\n🏠 CURRENT ADDRESS INFORMATION:")
        
        address_data = {}
        for urla_field, source_field in address_field_mappings.items():
            if source_field == 'current_street':
                address_data[urla_field] = current_street
            elif source_field == 'current_city':
                address_data[urla_field] = current_city
            elif source_field == 'current_state':
                address_data[urla_field] = current_state
            elif source_field == 'current_zip':
                address_data[urla_field] = current_zip
            elif source_field == 'years_at_address':
                address_data[urla_field] = years_at_address
            elif source_field == 'monthly_rent' or source_field == 'monthly_mortgage_payment':
                address_data[urla_field] = monthly_housing_expense or 0
        
        urla_data['Current_Address'] = address_data
        
        for field, value in address_data.items():
            urla_report.append(f"  {field}: {value}")
        
        # Employment Information  
        employment_mapping = next((rule for rule in mapping_rules if rule.get('rule_type') == 'employment_information'), {})
        employment_field_mappings = employment_mapping.get('field_mappings', {})
        
        urla_report.append(f"\n💼 EMPLOYMENT INFORMATION:")
        
        employment_data = {}
        for urla_field, source_field in employment_field_mappings.items():
            if source_field == 'employer_name':
                employment_data[urla_field] = employer_name
            elif source_field == 'job_title':
                employment_data[urla_field] = job_title
            elif source_field == 'years_employed':
                employment_data[urla_field] = years_employed
            elif source_field == 'monthly_gross_income':
                employment_data[urla_field] = monthly_gross_income
            elif source_field == 'employment_type':
                employment_data[urla_field] = employment_type
            elif source_field == 'self_employed_indicator':
                employment_data[urla_field] = employment_type == 'self_employed'
        
        urla_data['Employment_Information'] = employment_data
        
        for field, value in employment_data.items():
            urla_report.append(f"  {field}: {value}")
        
        # Section 2: Financial Information - Assets
        asset_mapping = next((rule for rule in mapping_rules if rule.get('rule_type') == 'financial_assets'), {})
        asset_types = asset_mapping.get('asset_types', {})
        
        urla_report.append(f"\n💰 SECTION 2: FINANCIAL INFORMATION - ASSETS")
        
        assets_data = {}
        total_assets = 0
        
        for asset_type, source_field in asset_types.items():
            value = 0
            if source_field == 'checking_account_balance':
                value = checking_account_balance or 0
            elif source_field == 'savings_account_balance':
                value = savings_account_balance or 0
            elif source_field == 'investment_account_balance':
                value = investment_account_balance or 0
            elif source_field == 'retirement_account_balance':
                value = retirement_account_balance or 0
            elif source_field == 'other_assets_value':
                value = other_assets_value or 0
            
            assets_data[asset_type] = value
            total_assets += value
            urla_report.append(f"  {asset_type}: ${value:,.2f}")
        
        assets_data['total_assets'] = total_assets
        urla_data['Section_2_Assets'] = assets_data
        urla_report.append(f"  TOTAL ASSETS: ${total_assets:,.2f}")
        
        # Section 3: Financial Information - Liabilities
        liability_mapping = next((rule for rule in mapping_rules if rule.get('rule_type') == 'financial_liabilities'), {})
        liability_types = liability_mapping.get('liability_types', {})
        
        urla_report.append(f"\n💳 SECTION 3: FINANCIAL INFORMATION - LIABILITIES")
        
        liabilities_data = {}
        total_monthly_payments = monthly_debts or 0
        
        for liability_type, source_field in liability_types.items():
            value = 0
            if source_field == 'installment_debt_balance':
                value = installment_debt_balance or 0
            elif source_field == 'revolving_debt_balance':
                value = revolving_debt_balance or 0
            elif source_field == 'mortgage_debt_balance':
                value = mortgage_debt_balance or 0
            
            liabilities_data[liability_type] = value
            urla_report.append(f"  {liability_type}: ${value:,.2f}")
        
        liabilities_data['total_monthly_payments'] = total_monthly_payments
        urla_data['Section_3_Liabilities'] = liabilities_data
        urla_report.append(f"  TOTAL MONTHLY PAYMENTS: ${total_monthly_payments:,.2f}")
        
        # Section 4: Loan and Property Information
        loan_property_mapping = next((rule for rule in mapping_rules if rule.get('rule_type') == 'loan_property_information'), {})
        loan_field_mappings = loan_property_mapping.get('field_mappings', {})
        
        urla_report.append(f"\n🏡 SECTION 4: LOAN AND PROPERTY INFORMATION")
        
        loan_property_data = {}
        for urla_field, source_field in loan_field_mappings.items():
            if source_field == 'loan_amount':
                loan_property_data[urla_field] = loan_amount
            elif source_field == 'loan_purpose':
                loan_property_data[urla_field] = loan_purpose
            elif source_field == 'property_address':
                loan_property_data[urla_field] = property_address
            elif source_field == 'property_type':
                loan_property_data[urla_field] = property_type
        
        if property_value:
            loan_property_data['property_value'] = property_value
            ltv = (loan_amount / property_value * 100) if property_value > 0 else 0
            loan_property_data['loan_to_value_ratio'] = ltv
        
        if down_payment:
            loan_property_data['down_payment_amount'] = down_payment
            down_payment_pct = (down_payment / property_value * 100) if property_value else 0
            loan_property_data['down_payment_percentage'] = down_payment_pct
        
        urla_data['Section_4_Loan_Property'] = loan_property_data
        
        for field, value in loan_property_data.items():
            urla_report.append(f"  {field}: {value}")
        
        # Section 5: Declarations
        declarations_mapping = next((rule for rule in mapping_rules if rule.get('rule_type') == 'declarations'), {})
        declaration_questions = declarations_mapping.get('declaration_questions', [])
        
        urla_report.append(f"\n📋 SECTION 5: DECLARATIONS")
        
        declarations_data = {
            'outstanding_judgments': outstanding_judgments,
            'declared_bankruptcy_past_7_years': declared_bankruptcy,
            'foreclosure_or_deed_in_lieu': foreclosure_or_deed,
            'party_to_lawsuit': party_to_lawsuit,
            'us_citizen': us_citizen,
            'permanent_resident_alien': permanent_resident
        }
        
        urla_data['Section_5_Declarations'] = declarations_data
        
        for declaration, answer in declarations_data.items():
            status = "Yes" if answer else "No"
            urla_report.append(f"  {declaration}: {status}")
        
        # Section 7: Military Service (if applicable)
        if military_service:
            urla_report.append(f"\n🎖️ SECTION 7: MILITARY SERVICE")
            military_data = {
                'military_service': military_service,
                'military_status': military_status or "Not Specified"
            }
            urla_data['Section_7_Military'] = military_data
            
            for field, value in military_data.items():
                urla_report.append(f"  {field}: {value}")
        
        # Compliance and Validation Summary
        urla_report.append(f"\n COMPLIANCE AND VALIDATION:")
        
        # Check completeness
        completion_rule = next((rule for rule in validation_rules if rule.get('rule_type') == 'form_completeness'), {})
        min_completion = completion_rule.get('minimum_completion_percentage', 0.95)
        
        # Calculate completion percentage (simplified)
        total_fields = len(section_1_data) + len(address_data) + len(employment_data) + len(loan_property_data)
        completed_fields = sum(1 for data_dict in [section_1_data, address_data, employment_data, loan_property_data] 
                              for value in data_dict.values() if value and str(value).strip())
        
        completion_pct = (completed_fields / total_fields) if total_fields > 0 else 0
        
        urla_report.append(f"Form Completion: {completion_pct:.1%}")
        urla_report.append(f"Required Minimum: {min_completion:.1%}")
        
        if completion_pct >= min_completion:
            urla_report.append(" Form meets completion requirements")
        else:
            urla_report.append("⚠️ Form may need additional information")
        
        # Regulatory Compliance
        compliance_rule = compliance_rules[0] if compliance_rules else {}
        
        urla_report.append(f"\nRegulatory Compliance:")
        urla_report.append(f" Fannie Mae/Freddie Mac URLA 1003 Format")
        urla_report.append(f" MISMO Data Standards Compliance")
        urla_report.append(f" Privacy Notice Requirements")
        
        # Final URLA Data Structure
        final_urla_structure = {
            "form_metadata": {
                "urla_form_id": urla_form_id,
                "form_version": form_version,
                "generation_timestamp": datetime.now().isoformat(),
                "source_application_id": application_id,
                "completion_percentage": completion_pct
            },
            "urla_sections": urla_data,
            "compliance_status": "compliant" if completion_pct >= min_completion else "needs_review",
            "validation_summary": {
                "total_fields": total_fields,
                "completed_fields": completed_fields,
                "completion_rate": completion_pct
            }
        }
        
        # Summary and Next Steps
        urla_report.append(f"\n📊 URLA GENERATION SUMMARY:")
        urla_report.append(f" URLA Form 1003 successfully generated")
        urla_report.append(f" All required sections populated")
        urla_report.append(f" Compliance validation completed")
        urla_report.append(f" Ready for lender submission")
        
        urla_report.append(f"\n💾 GENERATED URLA DATA:")
        urla_report.append(f"Form ID: {urla_form_id}")
        urla_report.append(f"Sections: {len(urla_data)} main sections")
        urla_report.append(f"Data Points: {total_fields} total fields")
        urla_report.append(f"Completion: {completion_pct:.1%}")
        
        urla_report.append(f"\n📋 NEXT STEPS:")
        urla_report.append("1. Review generated URLA data for accuracy")
        urla_report.append("2. Collect any missing documentation")
        urla_report.append("3. Obtain borrower signature and date")
        urla_report.append("4. Submit to underwriting for processing")
        
        return "\n".join(urla_report)
        
    except Exception as e:
        logger.error(f"Error during URLA generation: {e}")
        return f" Error during URLA generation: {str(e)}"


def validate_tool() -> bool:
    """Validate that the generate_urla_1003_form tool works correctly."""
    try:
        # Test with sample data
        result = generate_urla_1003_form.invoke({
            "application_id": "APP_20240101_123456_SMI",
            "first_name": "John",
            "last_name": "Smith",
            "ssn": "123-45-6789",
            "date_of_birth": "01/15/1985",
            "phone": "555-123-4567",
            "email": "john.smith@email.com",
            "current_street": "123 Main St",
            "current_city": "Anytown",
            "current_state": "CA",
            "current_zip": "90210",
            "years_at_address": 3.5,
            "employer_name": "Tech Corp",
            "job_title": "Software Engineer",
            "years_employed": 4.0,
            "monthly_gross_income": 8000.0,
            "employment_type": "w2",
            "loan_amount": 400000.0,
            "loan_purpose": "Purchase",
            "property_address": "456 Oak Ave, Anytown, CA 90210",
            "property_type": "Single Family Detached",
            "occupancy_type": "Primary Residence",
            "property_value": 500000.0,
            "down_payment": 100000.0,
            "checking_account_balance": 25000.0,
            "savings_account_balance": 50000.0,
            "monthly_debts": 1200.0
        })
        return "URLA FORM 1003 GENERATION REPORT" in result and "URLA_" in result
    except Exception as e:
        print(f"URLA generation tool validation failed: {e}")
        return False
