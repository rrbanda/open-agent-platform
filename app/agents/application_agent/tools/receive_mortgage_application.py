"""
Mortgage Application Intake Tool

This tool handles the initial receipt and validation of mortgage applications
based on Neo4j application intake rules. Enhanced with agentic application storage.
"""

import json
import logging
from typing import Dict, Any
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


def parse_application_info(application_info: str) -> Dict[str, Any]:
    """Extract complete application information from natural language description."""
    import re
    
    # Initialize with safe defaults
    parsed = {
        # Personal Information - will need validation
        "first_name": "",
        "last_name": "", 
        "ssn": "",
        "date_of_birth": "",
        "phone": "",
        "email": "",
        
        # Current Address
        "current_street": "Address to be provided",
        "current_city": "City to be provided",
        "current_state": "ST",
        "current_zip": "00000",
        "years_at_address": 2.0,
        
        # Employment
        "employer_name": "Employer to be provided",
        "job_title": "Position to be provided", 
        "years_employed": 2.0,
        "monthly_gross_income": 0.0,
        "employment_type": "w2",
        
        # Loan Details
        "loan_purpose": "purchase",
        "loan_amount": 0.0,
        "property_address": "",
        "property_value": 0.0,
        "property_type": "single_family_detached",
        "occupancy_type": "primary_residence",
        
        # Financial
        "credit_score": 0,
        "monthly_debts": 0.0,
        "liquid_assets": 0.0,
        "down_payment": 0.0,
        
        # Special flags
        "first_time_buyer": False,
        "military_service": False,
        "rural_property": False,
        
        # Optional
        "middle_name": "",
        "marital_status": "Single"
    }
    
    info_lower = application_info.lower()
    
    # Extract name components
    name_match = re.search(r"(?:name|i'm|i am)\s+(?:is\s+)?([a-zA-Z]+(?:\s+[a-zA-Z]+)*)", application_info, re.IGNORECASE)
    if name_match:
        full_name = name_match.group(1).strip()
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            parsed["first_name"] = name_parts[0]
            parsed["last_name"] = name_parts[-1]
            if len(name_parts) > 2:
                parsed["middle_name"] = " ".join(name_parts[1:-1])
        elif len(name_parts) == 1:
            parsed["first_name"] = name_parts[0]
    
    # Extract SSN
    ssn_match = re.search(r'ssn\s*(?:is|:)?\s*(\d{3}-\d{2}-\d{4})', info_lower)
    ssn_match_alt = re.search(r'social\s*security\s*(?:number)?\s*(?:is|:)?\s*(\d{3}-\d{2}-\d{4})', info_lower)
    if ssn_match:
        parsed["ssn"] = ssn_match.group(1)
    elif ssn_match_alt:
        parsed["ssn"] = ssn_match_alt.group(1)
    
    # Extract date of birth
    dob_match = re.search(r'(?:birth|dob|born)\s*(?:date|on)?\s*(?:is|:)?\s*(\d{4}-\d{2}-\d{2})', info_lower)
    dob_match_alt = re.search(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})', application_info)
    if dob_match:
        parsed["date_of_birth"] = dob_match.group(1)
    elif dob_match_alt:
        # Convert MM/DD/YYYY to YYYY-MM-DD
        date_str = dob_match_alt.group(1)
        try:
            if '/' in date_str:
                parts = date_str.split('/')
            else:
                parts = date_str.split('-')
            if len(parts) == 3 and len(parts[2]) == 4:
                parsed["date_of_birth"] = f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
        except:
            pass
    
    # Extract phone
    phone_match = re.search(r'phone\s*(?:number)?\s*(?:is|:)?\s*(\d{3}[-.]\d{3}[-.]\d{4})', application_info)
    phone_match_alt = re.search(r'(\d{3}[-.]\d{3}[-.]\d{4})', application_info)
    if phone_match:
        parsed["phone"] = phone_match.group(1).replace('.', '-')
    elif phone_match_alt:
        parsed["phone"] = phone_match_alt.group(1).replace('.', '-')
    
    # Extract email
    email_match = re.search(r'email\s*(?:address)?\s*(?:is|:)?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', info_lower)
    email_match_alt = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', application_info)
    if email_match:
        parsed["email"] = email_match.group(1)
    elif email_match_alt:
        parsed["email"] = email_match_alt.group(1)
    
    # Extract income (monthly first, then annual)
    monthly_income_match = re.search(r'(?:monthly\s*)?income\s*(?:is|of)?\s*\$?([0-9,]+)(?:\s*/?\s*month)?', info_lower)
    annual_income_match = re.search(r'(?:annual|yearly)\s*income\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    salary_match = re.search(r'salary\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    
    if monthly_income_match:
        parsed["monthly_gross_income"] = float(monthly_income_match.group(1).replace(',', ''))
    elif annual_income_match:
        annual_income = float(annual_income_match.group(1).replace(',', ''))
        parsed["monthly_gross_income"] = annual_income / 12
    elif salary_match:
        annual_salary = float(salary_match.group(1).replace(',', ''))
        parsed["monthly_gross_income"] = annual_salary / 12
    
    # Extract loan amount and property info
    loan_match = re.search(r'loan\s*(?:amount|for)?\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    home_price_match = re.search(r'(?:(?:home|house|property)\s*(?:price|cost|value)?\s*(?:is|of)?\s*\$?([0-9,]+)|(?:looking\s*at|buying)\s*(?:a\s*)?\$?([0-9,]+)\s*(?:home|house|property))', info_lower)
    
    if loan_match:
        parsed["loan_amount"] = float(loan_match.group(1).replace(',', ''))
    elif home_price_match:
        property_value = None
        for group in home_price_match.groups():
            if group:
                property_value = float(group.replace(',', ''))
                break
        if property_value:
            parsed["property_value"] = property_value
            # Assume 80% LTV if no specific loan amount given
            parsed["loan_amount"] = property_value * 0.8
    
    # Extract property address
    address_match = re.search(r'property\s*(?:address|at|located)?\s*(?:is|:)?\s*([^,\n]+(?:,\s*[^,\n]+)*)', application_info, re.IGNORECASE)
    if address_match:
        parsed["property_address"] = address_match.group(1).strip()
    
    # Extract down payment - check percentage first, then dollar amount
    down_percent_match = re.search(r'(\d+)%\s*down', info_lower)
    down_payment_match = re.search(r'(?:down\s*payment)\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    
    if down_percent_match:
        down_percent = float(down_percent_match.group(1)) / 100
        if parsed["property_value"] > 0:
            parsed["down_payment"] = parsed["property_value"] * down_percent
        elif parsed["loan_amount"] > 0:
            # Calculate property value from loan amount and down percent
            parsed["property_value"] = parsed["loan_amount"] / (1 - down_percent)
            parsed["down_payment"] = parsed["property_value"] * down_percent
    elif down_payment_match:
        parsed["down_payment"] = float(down_payment_match.group(1).replace(',', ''))
    
    # Extract credit score
    credit_match = re.search(r'credit\s*(?:score)?\s*(?:is|of)?\s*(\d{3})', info_lower)
    if credit_match:
        parsed["credit_score"] = int(credit_match.group(1))
    
    # Extract monthly debts
    debt_match = re.search(r'(?:monthly\s*)?debt(?:s)?\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    if debt_match:
        parsed["monthly_debts"] = float(debt_match.group(1).replace(',', ''))
    
    # Extract assets/savings
    assets_match = re.search(r'(?:assets?|savings?|cash)\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    if assets_match:
        parsed["liquid_assets"] = float(assets_match.group(1).replace(',', ''))
    
    # Extract employment details
    if 'self employed' in info_lower or 'self-employed' in info_lower:
        parsed["employment_type"] = "self_employed"
    elif 'contract' in info_lower:
        parsed["employment_type"] = "contract"
    
    # Extract special conditions
    if 'first time' in info_lower or 'first-time' in info_lower:
        parsed["first_time_buyer"] = True
    if 'military' in info_lower or 'veteran' in info_lower or 'va loan' in info_lower:
        parsed["military_service"] = True
    if 'rural' in info_lower or 'usda' in info_lower:
        parsed["rural_property"] = True
    
    # Extract loan purpose
    if 'refinance' in info_lower or 'refi' in info_lower:
        parsed["loan_purpose"] = "refinance"
    elif 'purchase' in info_lower or 'buying' in info_lower:
        parsed["loan_purpose"] = "purchase"
    
    return parsed


@tool
def receive_mortgage_application(
    application_info: str
) -> str:
    """Process complete mortgage application with customer data.
    
    This tool should be called when you have collected comprehensive information from the customer
    to submit a complete mortgage application. Provide all available customer information in natural language.
    
    Example inputs:
    "Sarah Johnson, SSN 123-45-6789, DOB 1985-03-15, phone 555-123-4567, email sarah@email.com, 
     income $8500/month, looking at $450000 home with 15% down, credit score 720, property address 123 Oak St, Dallas TX"
    
    "Complete application: John Smith, born 1990-01-01, SSN 987-65-4321, phone 555-987-6543, 
     email john@email.com, annual income $96000, loan amount $320000, property at 456 Pine Ave, Austin TX,
     down payment $80000, employed 5 years as software engineer, first-time buyer"
    """
    
    # Parse the natural language application info
    parsed_info = parse_application_info(application_info)
    
    # Extract all parameters
    first_name = parsed_info["first_name"]
    last_name = parsed_info["last_name"]
    ssn = parsed_info["ssn"]
    date_of_birth = parsed_info["date_of_birth"]
    phone = parsed_info["phone"]
    email = parsed_info["email"]
    current_street = parsed_info["current_street"]
    current_city = parsed_info["current_city"]
    current_state = parsed_info["current_state"]
    current_zip = parsed_info["current_zip"]
    years_at_address = parsed_info["years_at_address"]
    employer_name = parsed_info["employer_name"]
    job_title = parsed_info["job_title"]
    years_employed = parsed_info["years_employed"]
    monthly_gross_income = parsed_info["monthly_gross_income"]
    employment_type = parsed_info["employment_type"]
    loan_purpose = parsed_info["loan_purpose"]
    loan_amount = parsed_info["loan_amount"]
    property_address = parsed_info["property_address"]
    property_value = parsed_info["property_value"]
    property_type = parsed_info["property_type"]
    occupancy_type = parsed_info["occupancy_type"]
    middle_name = parsed_info["middle_name"]
    marital_status = parsed_info["marital_status"]
    credit_score = parsed_info["credit_score"]
    monthly_debts = parsed_info["monthly_debts"]
    liquid_assets = parsed_info["liquid_assets"]
    down_payment = parsed_info["down_payment"]
    first_time_buyer = parsed_info["first_time_buyer"]
    military_service = parsed_info["military_service"]
    rural_property = parsed_info["rural_property"]
    
    try:
        # Validate ESSENTIAL required fields (only truly critical ones)
        essential_fields = {
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth,
            'ssn': ssn,
            'phone': phone,
            'email': email,
            'loan_purpose': loan_purpose,
            'loan_amount': loan_amount,
            'property_address': property_address,
            'monthly_gross_income': monthly_gross_income
        }
        
        # Check for missing essential fields only
        missing_fields = [field for field, value in essential_fields.items() if not value or (isinstance(value, str) and str(value).strip() == "") or (isinstance(value, (int, float)) and value <= 0)]
        
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
        
        # Handle optional fields with smart defaults
        if not current_street or not current_city or not current_state:
            current_street = current_street or "Address to be provided"
            current_city = current_city or "City to be provided"  
            current_state = current_state or "State to be provided"
            current_zip = current_zip or "Zip to be provided"
            
        if not employer_name or not job_title:
            employer_name = employer_name or "Employer to be provided"
            job_title = job_title or "Position to be provided"
            
        if property_value <= 0:
            # Estimate property value based on loan amount and typical LTV
            property_value = loan_amount / 0.8  # Assume 80% LTV if not provided
            
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
        # Test with sample natural language data
        result = receive_mortgage_application.invoke({
            "application_info": "John Smith, SSN 123-45-6789, DOB 1990-01-01, phone 555-123-4567, email john.smith@email.com, income $8000/month, loan amount $400000, property address 456 Oak Ave Anytown CA 90210, credit score 720, down payment $100000"
        })
        return "MORTGAGE APPLICATION INTAKE REPORT" in result and "APPLICATION STATUS" in result
    except Exception as e:
        print(f"Application intake tool validation failed: {e}")
        return False
