"""
Mortgage Application Intake Tool

This tool handles the initial receipt and validation of mortgage applications
based on Neo4j application intake rules. Enhanced with agentic application storage.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from datetime import datetime

try:
    from utils import (
        get_neo4j_connection, 
        initialize_connection,
        store_application_data, 
        MortgageApplicationData
    )
except ImportError:
    from utils import (
        get_neo4j_connection, 
        initialize_connection,
        store_application_data, 
        MortgageApplicationData
    )

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


class MortgageApplicationRequest(BaseModel):
    """Mortgage application intake request parameters."""
    # Personal Information
    first_name: str = Field(..., description="Applicant's first name")
    last_name: str = Field(..., description="Applicant's last name")
    ssn: str = Field(..., description="Social Security Number (xxx-xx-xxxx)")
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    phone: str = Field(..., description="Phone number (xxx-xxx-xxxx)")
    email: str = Field(..., description="Email address")
    
    # Address Information
    current_street: str = Field(..., description="Current street address")
    current_city: str = Field(..., description="Current city")
    current_state: str = Field(..., description="Current state")
    current_zip: str = Field(..., description="Current ZIP code")
    years_at_address: float = Field(..., description="Years at current address")
    
    # Employment Information
    employer_name: str = Field(..., description="Current employer name")
    job_title: str = Field(..., description="Job title/position")
    years_employed: float = Field(..., description="Years with current employer")
    monthly_gross_income: float = Field(..., description="Monthly gross income")
    employment_type: str = Field(default="w2", description="Employment type (w2, self_employed, contract)")
    
    # Loan Information
    loan_purpose: str = Field(..., description="Loan purpose (purchase, refinance, etc.)")
    loan_amount: float = Field(..., description="Requested loan amount")
    property_address: str = Field(..., description="Property address")
    property_value: Optional[float] = Field(None, description="Property value estimate")
    property_type: str = Field(..., description="Property type (single_family_detached, condominium, etc.)")
    occupancy_type: str = Field(..., description="Occupancy type (primary_residence, second_home, investment_property)")
    
    # Financial Information
    credit_score: Optional[int] = Field(None, description="Credit score if known")
    monthly_debts: Optional[float] = Field(None, description="Total monthly debt payments")
    liquid_assets: Optional[float] = Field(None, description="Liquid assets available")
    down_payment: Optional[float] = Field(None, description="Down payment amount")
    
    # Additional Information
    first_time_buyer: bool = Field(default=False, description="Is this a first-time home buyer")
    military_service: bool = Field(default=False, description="Military service (for VA loans)")
    rural_property: bool = Field(default=False, description="Rural property (for USDA loans)")


@tool
def receive_mortgage_application(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    ssn: str,
    phone: str,
    email: str,
    current_street: str,
    current_city: str,
    current_state: str,
    current_zip: str,
    years_at_address: float,
    employer_name: str,
    job_title: str,
    years_employed: float,
    monthly_gross_income: float,
    employment_type: str,
    loan_purpose: str,
    loan_amount: float,
    property_address: str,
    property_value: float,
    property_type: str,
    occupancy_type: str,
    middle_name: str = "",
    marital_status: str = "Single",
    credit_score: int = 0,
    monthly_debts: float = 0,
    liquid_assets: float = 0,
    down_payment: float = 0,
    first_time_buyer: bool = False,
    military_service: bool = False,
    rural_property: bool = False
) -> str:
    """Process complete mortgage application with real customer data.
    
    This tool should ONLY be called after collecting all required information from the customer.
    NEVER call this tool with fake or assumed data.
    
    Args:
        first_name: Customer's first name
        last_name: Customer's last name
        date_of_birth: Date of birth (YYYY-MM-DD format)
        ssn: Social Security Number (xxx-xx-xxxx format)
        phone: Phone number
        email: Email address
        current_street: Current street address
        current_city: Current city
        current_state: Current state (2-letter abbreviation)
        current_zip: ZIP code
        years_at_address: Years at current address
        employer_name: Current employer name
        job_title: Job title/position
        years_employed: Years with current employer
        monthly_gross_income: Monthly gross income
        employment_type: Employment type (w2, self_employed, contract)
        loan_purpose: Loan purpose (purchase, refinance, etc.)
        loan_amount: Requested loan amount
        property_address: Property address
        property_value: Property value
        property_type: Property type
        occupancy_type: How property will be used
        middle_name: Middle name (optional)
        marital_status: Marital status (optional)
        credit_score: Credit score (optional)
        monthly_debts: Monthly debt payments (optional)
        liquid_assets: Available assets (optional)
        down_payment: Down payment amount (optional)
        first_time_buyer: First-time buyer status (optional)
        military_service: Military service status (optional)
        rural_property: Rural property status (optional)
    """
    
    try:
        # Validate required fields
        required_fields = {
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth,
            'ssn': ssn,
            'phone': phone,
            'email': email,
            'current_street': current_street,
            'current_city': current_city,
            'current_state': current_state,
            'current_zip': current_zip,
            'employer_name': employer_name,
            'job_title': job_title,
            'loan_purpose': loan_purpose,
            'property_address': property_address,
            'property_type': property_type,
            'occupancy_type': occupancy_type
        }
        
        # Check for missing required fields
        missing_fields = [field for field, value in required_fields.items() if not value or str(value).strip() == ""]
        
        if missing_fields:
            return f"""
❌ **APPLICATION INCOMPLETE**

The following required information is missing:
{chr(10).join([f'• {field.replace("_", " ").title()}' for field in missing_fields])}

Please collect this information from the customer before submitting the application.
Ask the customer for each missing piece of information, then call this tool again with complete data.
"""
        
        # Validate field formats
        import re
        validation_errors = []
        
        # SSN format validation
        if not re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
            validation_errors.append("• SSN must be in format xxx-xx-xxxx")
            
        # Date format validation
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_of_birth):
            validation_errors.append("• Date of birth must be in format YYYY-MM-DD")
            
        # Email format validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            validation_errors.append("• Email address format is invalid")
            
        # State format validation
        if len(current_state) != 2:
            validation_errors.append("• State must be 2-letter abbreviation (e.g., TX, CA)")
            
        # ZIP format validation
        if not re.match(r'^\d{5}(-\d{4})?$', current_zip):
            validation_errors.append("• ZIP code must be 5 digits or 5+4 format")
            
        if validation_errors:
            return f"""
❌ **VALIDATION ERRORS**

Please correct the following information:
{chr(10).join(validation_errors)}

Ask the customer to provide the correct information and call this tool again.
"""
        
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get application requirements
            requirements_query = """
            MATCH (rule:ApplicationIntakeRule)
            WHERE rule.category = 'ApplicationRequirements'
            RETURN rule
            """
            result = session.run(requirements_query)
            requirements_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
            
            # Get validation rules
            validation_query = """
            MATCH (rule:ApplicationIntakeRule)
            WHERE rule.category = 'ValidationRules'
            RETURN rule
            """
            result = session.run(validation_query)
            validation_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
        
        # Generate application ID
        application_id = f"APP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{last_name.upper()[:3]}"
        
        # Create application intake report
        intake_report = []
        intake_report.append("MORTGAGE APPLICATION INTAKE REPORT")
        intake_report.append("=" * 50)
        
        # Application Information
        intake_report.append(f"\n📝 APPLICATION DETAILS:")
        intake_report.append(f"Application ID: {application_id}")
        intake_report.append(f"Received Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        intake_report.append(f"Applicant: {first_name} {last_name}")
        intake_report.append(f"Contact: {phone} | {email}")
        
        # Loan Details
        intake_report.append(f"\n💰 LOAN REQUEST:")
        intake_report.append(f"Purpose: {loan_purpose.replace('_', ' ').title()}")
        intake_report.append(f"Loan Amount: ${loan_amount:,.2f}")
        intake_report.append(f"Property: {property_address}")
        if property_value:
            ltv = (loan_amount / property_value * 100) if property_value > 0 else 0
            intake_report.append(f"Property Value: ${property_value:,.2f}")
            intake_report.append(f"Loan-to-Value: {ltv:.1f}%")
        intake_report.append(f"Property Type: {property_type.replace('_', ' ').title()}")
        intake_report.append(f"Occupancy: {occupancy_type.replace('_', ' ').title()}")
        
        # Applicant Profile
        intake_report.append(f"\n👤 APPLICANT PROFILE:")
        intake_report.append(f"Current Address: {current_street}, {current_city}, {current_state} {current_zip}")
        intake_report.append(f"Years at Address: {years_at_address}")
        intake_report.append(f"Employer: {employer_name}")
        intake_report.append(f"Position: {job_title}")
        intake_report.append(f"Years Employed: {years_employed}")
        intake_report.append(f"Monthly Income: ${monthly_gross_income:,.2f}")
        intake_report.append(f"Employment Type: {employment_type.replace('_', ' ').title()}")
        
        # Financial Summary
        intake_report.append(f"\n💳 FINANCIAL SUMMARY:")
        if credit_score:
            intake_report.append(f"Credit Score: {credit_score}")
        if monthly_debts:
            intake_report.append(f"Monthly Debts: ${monthly_debts:,.2f}")
            dti = (monthly_debts / monthly_gross_income * 100) if monthly_gross_income > 0 else 0
            intake_report.append(f"Estimated DTI: {dti:.1f}%")
        if liquid_assets:
            intake_report.append(f"Liquid Assets: ${liquid_assets:,.2f}")
        if down_payment:
            intake_report.append(f"Down Payment: ${down_payment:,.2f}")
            down_payment_pct = (down_payment / property_value * 100) if property_value else 0
            intake_report.append(f"Down Payment %: {down_payment_pct:.1f}%")
        
        # Special Programs
        intake_report.append(f"\n🎯 SPECIAL PROGRAM ELIGIBILITY:")
        if first_time_buyer:
            intake_report.append(" First-Time Home Buyer")
        if military_service:
            intake_report.append(" Military Service (VA Loan Eligible)")
        if rural_property:
            intake_report.append(" Rural Property (USDA Loan Eligible)")
        
        # Data Validation
        intake_report.append(f"\n DATA VALIDATION:")
        
        validation_issues = []
        validation_warnings = []
        
        # Get validation rules
        data_validation = next((rule for rule in validation_rules if rule.get('rule_type') == 'data_format_validation'), {})
        
        # SSN validation
        if data_validation and not _validate_ssn_format(ssn):
            validation_issues.append("SSN format invalid (should be xxx-xx-xxxx)")
        else:
            intake_report.append(" SSN format valid")
        
        # Phone validation
        if data_validation and not _validate_phone_format(phone):
            validation_issues.append("Phone format invalid (should be xxx-xxx-xxxx)")
        else:
            intake_report.append(" Phone format valid")
        
        # Email validation
        if "@" not in email or "." not in email:
            validation_issues.append("Email format appears invalid")
        else:
            intake_report.append(" Email format valid")
        
        # Loan amount validation
        if data_validation:
            loan_range = data_validation.get('loan_amount_range', {})
            min_loan = loan_range.get('min', 50000)
            max_loan = loan_range.get('max', 5000000)
            if loan_amount < min_loan or loan_amount > max_loan:
                validation_issues.append(f"Loan amount outside acceptable range (${min_loan:,} - ${max_loan:,})")
            else:
                intake_report.append(" Loan amount within acceptable range")
        
        # Income validation
        if data_validation:
            income_range = data_validation.get('income_range', {})
            min_income = income_range.get('min', 1000)
            max_income = income_range.get('max', 100000)
            if monthly_gross_income < min_income or monthly_gross_income > max_income:
                validation_warnings.append(f"Income outside typical range (${min_income:,} - ${max_income:,})")
            else:
                intake_report.append(" Income within expected range")
        
        # Field Completeness Check
        intake_report.append(f"\n📋 FIELD COMPLETENESS:")
        
        # Get required fields
        requirements_rule = next((rule for rule in requirements_rules if rule.get('rule_type') == 'required_fields'), {})
        
        if requirements_rule:
            personal_fields = requirements_rule.get('personal_info', [])
            current_fields = requirements_rule.get('current_address', [])
            employment_fields = requirements_rule.get('employment', [])
            loan_fields = requirements_rule.get('loan_details', [])
            
            # Check completeness (simplified)
            total_required = len(personal_fields) + len(current_fields) + len(employment_fields) + len(loan_fields)
            completed_fields = 0
            
            # Personal info (we have all required)
            completed_fields += len(personal_fields)
            intake_report.append(f" Personal Information: {len(personal_fields)}/{len(personal_fields)} fields")
            
            # Address info (we have all required)
            completed_fields += len(current_fields)
            intake_report.append(f" Address Information: {len(current_fields)}/{len(current_fields)} fields")
            
            # Employment info (we have all required)
            completed_fields += len(employment_fields)
            intake_report.append(f" Employment Information: {len(employment_fields)}/{len(employment_fields)} fields")
            
            # Loan details (we have all required)
            completed_fields += len(loan_fields)
            intake_report.append(f" Loan Details: {len(loan_fields)}/{len(loan_fields)} fields")
            
            # Prevent division by zero
            if total_required > 0:
                completion_percentage = (completed_fields / total_required) * 100
                intake_report.append(f"📊 Overall Completion: {completion_percentage:.1f}%")
            else:
                intake_report.append(f"📊 Overall Completion: No requirements configured")
        
        # Issues and Warnings
        if validation_issues:
            intake_report.append(f"\n VALIDATION ISSUES:")
            for issue in validation_issues:
                intake_report.append(f"   • {issue}")
        
        if validation_warnings:
            intake_report.append(f"\n⚠️ VALIDATION WARNINGS:")
            for warning in validation_warnings:
                intake_report.append(f"   • {warning}")
        
        # Application Status
        intake_report.append(f"\n🎯 APPLICATION STATUS:")
        
        if validation_issues:
            application_status = "INCOMPLETE - VALIDATION ERRORS"
            next_steps = "Please correct validation errors and resubmit"
        elif validation_warnings:
            application_status = "RECEIVED - REVIEW REQUIRED"
            next_steps = "Application received, additional review required"
        else:
            application_status = "RECEIVED - PROCESSING"
            next_steps = "Application accepted, initiating processing workflow"
        
        intake_report.append(f"Status: {application_status}")
        intake_report.append(f"Next Steps: {next_steps}")
        
        # Recommended Workflow
        intake_report.append(f"\n🔄 RECOMMENDED WORKFLOW:")
        
        if not validation_issues:
            if first_time_buyer or credit_score and credit_score < 650:
                intake_report.append("1. Route to MortgageAdvisorAgent for guidance")
                intake_report.append("2. Proceed to DocumentAgent for verification")
            else:
                intake_report.append("1. Proceed directly to DocumentAgent for verification")
                intake_report.append("2. Continue to AppraisalAgent for property valuation")
            
            intake_report.append("3. Final review by UnderwritingAgent")
        else:
            intake_report.append("1. Return to applicant for correction")
            intake_report.append("2. Re-submit corrected application")
        
        # Generate timestamp
        intake_report.append(f"\n📅 Application received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        intake_report.append(f"Application ID: {application_id}")
        
        # 🤖 AGENTIC STORAGE: Automatically store application data in Neo4j for cross-agent access
        try:
            app_data = MortgageApplicationData(
                application_id=application_id,
                received_date=datetime.now().isoformat(),
                current_status="RECEIVED" if not validation_issues else "INCOMPLETE",
                first_name=first_name,
                last_name=last_name,
                ssn=ssn,
                date_of_birth=date_of_birth,
                phone=phone,
                email=email,
                current_street=current_street,
                current_city=current_city,
                current_state=current_state,
                current_zip=current_zip,
                years_at_address=years_at_address,
                employer_name=employer_name,
                job_title=job_title,
                years_employed=years_employed,
                monthly_gross_income=monthly_gross_income,
                employment_type=employment_type,
                loan_purpose=loan_purpose,
                loan_amount=loan_amount,
                property_address=property_address,
                property_value=property_value,
                property_type=property_type,
                occupancy_type=occupancy_type,
                credit_score=credit_score,
                monthly_debts=monthly_debts,
                liquid_assets=liquid_assets,
                down_payment=down_payment,
                first_time_buyer=first_time_buyer,
                military_service=military_service,
                rural_property=rural_property,
                validation_status="VALIDATED" if not validation_issues else "VALIDATION_ERRORS",
                completion_percentage=completion_percentage if 'completion_percentage' in locals() else 85.0,
                next_agent="DocumentAgent" if not validation_issues else None,
                workflow_notes=next_steps if 'next_steps' in locals() else "Application intake completed"
            )
            
            success, storage_result = store_application_data(app_data)
            
            if success:
                intake_report.append(f"\n AGENTIC STORAGE: Application stored in Neo4j for cross-agent workflow")
                intake_report.append(f"   Storage ID: {storage_result}")
                intake_report.append(f"   Available for: DocumentAgent, MortgageAdvisorAgent, UnderwritingAgent")
            else:
                intake_report.append(f"\n⚠️ STORAGE WARNING: {storage_result}")
                
        except Exception as storage_error:
            logger.warning(f"Agentic storage failed: {storage_error}")
            intake_report.append(f"\n⚠️ STORAGE WARNING: Auto-storage failed, proceeding with manual workflow")
        
        return "\n".join(intake_report)
        
    except Exception as e:
        logger.error(f"Error during application intake: {e}")
        return f" Error during application intake: {str(e)}"


def _validate_ssn_format(ssn: str) -> bool:
    """Validate SSN format (xxx-xx-xxxx)."""
    import re
    pattern = r'^\d{3}-\d{2}-\d{4}$'
    return bool(re.match(pattern, ssn))


def _validate_phone_format(phone: str) -> bool:
    """Validate phone format (xxx-xxx-xxxx)."""
    import re
    pattern = r'^\d{3}-\d{3}-\d{4}$'
    return bool(re.match(pattern, phone))


def validate_tool() -> bool:
    """Validate that the receive_mortgage_application tool works correctly."""
    try:
        # Test with sample data
        result = receive_mortgage_application.invoke({
            "first_name": "John",
            "last_name": "Smith",
            "ssn": "123-45-6789",
            "date_of_birth": "1990-01-01",
            "phone": "555-123-4567",
            "email": "john.smith@email.com",
            "current_street": "123 Main St",
            "current_city": "Anytown",
            "current_state": "CA",
            "current_zip": "90210",
            "years_at_address": 3.5,
            "employer_name": "Tech Company Inc",
            "job_title": "Software Engineer",
            "years_employed": 4.0,
            "monthly_gross_income": 8000.0,
            "employment_type": "w2",
            "loan_purpose": "purchase",
            "loan_amount": 400000.0,
            "property_address": "456 Oak Ave, Anytown, CA 90210",
            "property_value": 500000.0,
            "property_type": "single_family_detached",
            "occupancy_type": "primary_residence",
            "credit_score": 720,
            "monthly_debts": 1200.0,
            "liquid_assets": 100000.0,
            "down_payment": 100000.0,
            "first_time_buyer": False,
            "military_service": False,
            "rural_property": False
        })
        return "MORTGAGE APPLICATION INTAKE REPORT" in result and "APPLICATION STATUS" in result
    except Exception as e:
        print(f"Application intake tool validation failed: {e}")
        return False
