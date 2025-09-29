"""
Initial Qualification Assessment Tool

This tool performs initial qualification and pre-screening
based on Neo4j application intake rules.
"""

import json
import logging
from typing import Dict, Any
from langchain_core.tools import tool

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


def parse_borrower_info(borrower_info: str) -> Dict[str, Any]:
    """Extract key financial information from natural language borrower description."""
    import re
    
    # Initialize with safe defaults
    parsed = {
        "credit_score": 650,  # Default middle credit score
        "monthly_gross_income": 5000.0,
        "monthly_debts": 500.0, 
        "liquid_assets": 20000.0,
        "employment_years": 2.0,
        "employment_type": "w2",
        "loan_amount": 300000.0,
        "property_value": 375000.0,  # 20% down assumption
        "down_payment": 60000.0,  # 20% down assumption
        "property_type": "single_family_detached",
        "occupancy_type": "primary_residence", 
        "loan_purpose": "purchase",
        "application_id": "TEMP_QUALIFICATION",
        "first_time_buyer": False,
        "military_service": False,
        "rural_property": False,
        "bankruptcy_history": False,
        "foreclosure_history": False,
        "collections_amount": 0.0,
        "late_payments_12_months": 0
    }
    
    info_lower = borrower_info.lower()
    
    # Extract credit score
    credit_match = re.search(r'credit\s*(?:score)?\s*(?:is|of)?\s*(\d{3})', info_lower)
    if credit_match:
        parsed["credit_score"] = int(credit_match.group(1))
    
    # Extract monthly income - look for monthly first, then annual
    monthly_income_match = re.search(r'(?:monthly\s*)?income\s*(?:is|of)?\s*\$?([0-9,]+)(?:\s*/?\s*month)?', info_lower)
    annual_income_match = re.search(r'(?:annual|yearly)\s*income\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    salary_match = re.search(r'salary\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    
    if monthly_income_match:
        parsed["monthly_gross_income"] = float(monthly_income_match.group(1).replace(',', ''))
    elif annual_income_match:
        annual_income = float(annual_income_match.group(1).replace(',', ''))
        parsed["monthly_gross_income"] = annual_income / 12
    elif salary_match:
        # Assume salary is annual
        annual_salary = float(salary_match.group(1).replace(',', ''))
        parsed["monthly_gross_income"] = annual_salary / 12
    
    # Extract loan amount
    loan_match = re.search(r'loan\s*(?:amount|for)?\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    # More flexible home price matching
    home_price_match = re.search(r'(?:(?:home|house|property)\s*(?:price|cost|value)?\s*(?:is|of)?\s*\$?([0-9,]+)|(?:looking\s*at|buying)\s*(?:a\s*)?\$?([0-9,]+)\s*(?:home|house|property))', info_lower)
    
    if loan_match:
        parsed["loan_amount"] = float(loan_match.group(1).replace(',', ''))
    elif home_price_match:
        # Handle multiple capture groups
        property_value = None
        for group in home_price_match.groups():
            if group:
                property_value = float(group.replace(',', ''))
                break
        parsed["property_value"] = property_value
        # Assume 20% down payment
        parsed["loan_amount"] = property_value * 0.8
        parsed["down_payment"] = property_value * 0.2
    
    # Extract down payment
    down_payment_match = re.search(r'(?:down\s*payment|down)\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    down_percent_match = re.search(r'(\d+)%\s*down', info_lower)
    
    if down_payment_match:
        parsed["down_payment"] = float(down_payment_match.group(1).replace(',', ''))
        # Calculate property value if not already set
        if parsed["property_value"] == 375000.0:  # default value
            parsed["property_value"] = parsed["loan_amount"] + parsed["down_payment"]
    elif down_percent_match:
        down_percent = float(down_percent_match.group(1)) / 100
        if parsed["property_value"] > 375000.0 or loan_match:  # We have property value or loan amount
            if parsed["property_value"] == 375000.0:  # Use loan amount
                parsed["property_value"] = parsed["loan_amount"] / (1 - down_percent)
            parsed["down_payment"] = parsed["property_value"] * down_percent
            parsed["loan_amount"] = parsed["property_value"] - parsed["down_payment"]
    
    # Extract monthly debts
    debt_match = re.search(r'(?:monthly\s*)?debt(?:s)?\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    if debt_match:
        parsed["monthly_debts"] = float(debt_match.group(1).replace(',', ''))
    
    # Extract assets/savings
    assets_match = re.search(r'(?:assets?|savings?|cash)\s*(?:is|of)?\s*\$?([0-9,]+)', info_lower)
    if assets_match:
        parsed["liquid_assets"] = float(assets_match.group(1).replace(',', ''))
    
    # Extract employment information
    if 'self employed' in info_lower or 'self-employed' in info_lower:
        parsed["employment_type"] = "self_employed"
    elif 'contract' in info_lower:
        parsed["employment_type"] = "contract"
    
    employment_match = re.search(r'(\d+)\s*years?\s*(?:employed|job|work)', info_lower)
    if employment_match:
        parsed["employment_years"] = float(employment_match.group(1))
    
    # Extract special conditions
    if 'first time' in info_lower or 'first-time' in info_lower:
        parsed["first_time_buyer"] = True
    if 'military' in info_lower or 'veteran' in info_lower or 'va loan' in info_lower:
        parsed["military_service"] = True
    if 'rural' in info_lower or 'usda' in info_lower:
        parsed["rural_property"] = True
    if 'bankruptcy' in info_lower:
        parsed["bankruptcy_history"] = True
    if 'foreclosure' in info_lower:
        parsed["foreclosure_history"] = True
    
    return parsed


@tool  
def perform_initial_qualification(
    borrower_info: str
) -> str:
    """
    Perform initial qualification assessment using Neo4j application intake rules.
    
    This tool evaluates initial qualification across multiple loan programs
    and provides routing recommendations for the application workflow.
    
    Provide borrower information in natural language, such as:
    "Credit score is 720, monthly income $8,500, looking at $450,000 home with 15% down"
    "I make $75,000 annually, credit score 680, have $30,000 saved for down payment"
    "Self-employed 3 years, monthly income $6,000, credit 710, loan amount $350,000"
    """
    
    # Parse the natural language input
    parsed_info = parse_borrower_info(borrower_info)
    
    # Extract all the parameters
    credit_score = parsed_info["credit_score"]
    monthly_gross_income = parsed_info["monthly_gross_income"]  
    monthly_debts = parsed_info["monthly_debts"]
    liquid_assets = parsed_info["liquid_assets"]
    employment_years = parsed_info["employment_years"]
    employment_type = parsed_info["employment_type"]
    loan_amount = parsed_info["loan_amount"]
    property_value = parsed_info["property_value"]
    down_payment = parsed_info["down_payment"]
    property_type = parsed_info["property_type"]
    occupancy_type = parsed_info["occupancy_type"]
    loan_purpose = parsed_info["loan_purpose"]
    application_id = parsed_info["application_id"]
    first_time_buyer = parsed_info["first_time_buyer"]
    military_service = parsed_info["military_service"]
    rural_property = parsed_info["rural_property"]
    bankruptcy_history = parsed_info["bankruptcy_history"]
    foreclosure_history = parsed_info["foreclosure_history"]
    collections_amount = parsed_info["collections_amount"]
    late_payments_12_months = parsed_info["late_payments_12_months"]
    
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get initial qualification rules
            qualification_query = """
            MATCH (rule:ApplicationIntakeRule)
            WHERE rule.category = 'InitialQualification'
            RETURN rule
            """
            result = session.run(qualification_query)
            qualification_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
        
        # Calculate key ratios
        ltv = (loan_amount / property_value * 100) if property_value > 0 else 0
        down_payment_pct = (down_payment / property_value * 100) if property_value > 0 else 0
        front_end_dti = ((loan_amount * 0.005) / monthly_gross_income * 100) if monthly_gross_income > 0 else 0  # Estimated
        back_end_dti = ((monthly_debts + (loan_amount * 0.005)) / monthly_gross_income * 100) if monthly_gross_income > 0 else 0
        debt_to_income = (monthly_debts / monthly_gross_income * 100) if monthly_gross_income > 0 else 0
        
        # Generate qualification report
        qualification_report = []
        qualification_report.append("INITIAL QUALIFICATION ASSESSMENT")
        qualification_report.append("=" * 50)
        
        # Application Summary
        qualification_report.append(f"\n📋 APPLICATION SUMMARY:")
        qualification_report.append(f"Application ID: {application_id}")
        qualification_report.append(f"Loan Purpose: {loan_purpose.replace('_', ' ').title()}")
        qualification_report.append(f"Loan Amount: ${loan_amount:,.2f}")
        qualification_report.append(f"Property Value: ${property_value:,.2f}")
        qualification_report.append(f"Down Payment: ${down_payment:,.2f} ({down_payment_pct:.1f}%)")
        qualification_report.append(f"LTV Ratio: {ltv:.1f}%")
        
        # Borrower Profile
        qualification_report.append(f"\n👤 BORROWER PROFILE:")
        qualification_report.append(f"Credit Score: {credit_score}")
        qualification_report.append(f"Monthly Income: ${monthly_gross_income:,.2f}")
        qualification_report.append(f"Monthly Debts: ${monthly_debts:,.2f}")
        qualification_report.append(f"DTI Ratio: {debt_to_income:.1f}%")
        qualification_report.append(f"Liquid Assets: ${liquid_assets:,.2f}")
        qualification_report.append(f"Employment: {employment_type.replace('_', ' ').title()} ({employment_years} years)")
        
        # Special Considerations
        qualification_report.append(f"\n🎯 SPECIAL CONSIDERATIONS:")
        if first_time_buyer:
            qualification_report.append(" First-Time Home Buyer")
        if military_service:
            qualification_report.append(" Military Service (VA Eligible)")
        if rural_property:
            qualification_report.append(" Rural Property (USDA Eligible)")
        if bankruptcy_history:
            qualification_report.append("⚠️ Bankruptcy History")
        if foreclosure_history:
            qualification_report.append("⚠️ Foreclosure History")
        if collections_amount > 0:
            qualification_report.append(f"⚠️ Collections: ${collections_amount:,.2f}")
        if late_payments_12_months > 0:
            qualification_report.append(f"⚠️ Late Payments (12 months): {late_payments_12_months}")
        
        # Get qualification rules
        credit_rule = next((rule for rule in qualification_rules if rule.get('rule_type') == 'credit_pre_screen'), {})
        income_rule = next((rule for rule in qualification_rules if rule.get('rule_type') == 'income_pre_screen'), {})
        asset_rule = next((rule for rule in qualification_rules if rule.get('rule_type') == 'asset_pre_screen'), {})
        
        # Credit Assessment
        qualification_report.append(f"\n🔍 CREDIT ASSESSMENT:")
        
        credit_issues = []
        credit_warnings = []
        
        # Check minimum credit scores
        min_scores = credit_rule.get('minimum_credit_scores', {})
        auto_decline = credit_rule.get('auto_decline_conditions', [])
        manual_review = credit_rule.get('manual_review_triggers', [])
        
        qualification_report.append(f"Credit Score: {credit_score}")
        
        # Check each loan program
        program_eligibility = {}
        for program, min_score in min_scores.items():
            if credit_score >= min_score:
                program_eligibility[program] = "ELIGIBLE"
                qualification_report.append(f"   {program.upper()}: Eligible (min {min_score})")
            else:
                program_eligibility[program] = "INELIGIBLE"
                qualification_report.append(f"   {program.upper()}: Below minimum (min {min_score})")
        
        # Check auto-decline conditions
        if credit_score < 500:
            credit_issues.append("Credit score below 500 - auto decline")
        if bankruptcy_history:
            credit_issues.append("Recent bankruptcy - requires seasoning verification")
        if foreclosure_history:
            credit_issues.append("Foreclosure history - requires seasoning verification")
        
        # Check manual review triggers
        if 580 <= credit_score <= 620:
            credit_warnings.append("Credit score in manual review range")
        if collections_amount > 5000:
            credit_warnings.append("Significant collections amount")
        if late_payments_12_months > 2:
            credit_warnings.append("Multiple recent late payments")
        
        # Income Assessment
        qualification_report.append(f"\n💰 INCOME ASSESSMENT:")
        
        income_issues = []
        income_warnings = []
        
        # Check minimum income requirements
        min_income = income_rule.get('minimum_income_requirements', {})
        single_min = min_income.get('single_borrower', 3000)
        
        if monthly_gross_income >= single_min:
            qualification_report.append(f" Income: ${monthly_gross_income:,.2f} (min ${single_min:,.2f})")
        else:
            qualification_report.append(f" Income: ${monthly_gross_income:,.2f} (below min ${single_min:,.2f})")
            income_issues.append(f"Income below minimum requirement")
        
        # Check employment stability
        stability_reqs = income_rule.get('income_stability_requirements', {})
        min_employment = stability_reqs.get('employment_months', 24) / 12
        self_employed_years = stability_reqs.get('self_employed_years', 2)
        
        if employment_type == "self_employed":
            if employment_years >= self_employed_years:
                qualification_report.append(f" Self-Employment: {employment_years} years (min {self_employed_years})")
            else:
                qualification_report.append(f" Self-Employment: {employment_years} years (min {self_employed_years})")
                income_issues.append("Insufficient self-employment history")
        else:
            if employment_years >= min_employment:
                qualification_report.append(f" Employment: {employment_years} years (min {min_employment})")
            else:
                qualification_report.append(f"⚠️ Employment: {employment_years} years (min {min_employment})")
                income_warnings.append("Limited employment history")
        
        # Check DTI ratios
        dti_limits = income_rule.get('dti_pre_screen_limits', {})
        front_end_limit = dti_limits.get('front_end', 0.31) * 100
        back_end_limit = dti_limits.get('back_end', 0.45) * 100
        
        if front_end_dti <= front_end_limit:
            qualification_report.append(f" Front-End DTI: {front_end_dti:.1f}% (max {front_end_limit:.1f}%)")
        else:
            qualification_report.append(f"⚠️ Front-End DTI: {front_end_dti:.1f}% (max {front_end_limit:.1f}%)")
            income_warnings.append("Front-end DTI above preferred limits")
        
        if back_end_dti <= back_end_limit:
            qualification_report.append(f" Back-End DTI: {back_end_dti:.1f}% (max {back_end_limit:.1f}%)")
        else:
            qualification_report.append(f" Back-End DTI: {back_end_dti:.1f}% (max {back_end_limit:.1f}%)")
            income_issues.append("Back-end DTI exceeds limits")
        
        # Asset Assessment
        qualification_report.append(f"\n💳 ASSET ASSESSMENT:")
        
        asset_issues = []
        asset_warnings = []
        
        # Check down payment requirements
        min_down_payments = asset_rule.get('minimum_down_payment', {})
        
        for program, min_down_pct in min_down_payments.items():
            min_down_amount = property_value * min_down_pct
            if program in program_eligibility and program_eligibility[program] == "ELIGIBLE":
                if down_payment >= min_down_amount:
                    qualification_report.append(f" {program.upper()}: Down payment ${down_payment:,.0f} (min {min_down_pct*100:.1f}%)")
                else:
                    qualification_report.append(f" {program.upper()}: Down payment ${down_payment:,.0f} (min ${min_down_amount:,.0f})")
                    program_eligibility[program] = "INSUFFICIENT_FUNDS"
        
        # Check reserve requirements
        reserve_reqs = asset_rule.get('reserve_requirements', {})
        required_reserves = reserve_reqs.get(occupancy_type, "2_months_payment")
        estimated_payment = loan_amount * 0.005  # Rough estimate
        
        if "2_months" in required_reserves:
            required_reserve_amount = estimated_payment * 2
        elif "4_months" in required_reserves:
            required_reserve_amount = estimated_payment * 4
        elif "6_months" in required_reserves:
            required_reserve_amount = estimated_payment * 6
        else:
            required_reserve_amount = estimated_payment * 2
        
        available_after_down = liquid_assets - down_payment
        if available_after_down >= required_reserve_amount:
            qualification_report.append(f" Reserves: ${available_after_down:,.0f} (min ${required_reserve_amount:,.0f})")
        else:
            qualification_report.append(f"⚠️ Reserves: ${available_after_down:,.0f} (min ${required_reserve_amount:,.0f})")
            asset_warnings.append("Insufficient reserves after down payment")
        
        # Program Eligibility Summary
        qualification_report.append(f"\n🎯 LOAN PROGRAM ELIGIBILITY:")
        
        eligible_programs = []
        ineligible_programs = []
        
        for program, status in program_eligibility.items():
            if status == "ELIGIBLE":
                eligible_programs.append(program)
                qualification_report.append(f" {program.upper()}: ELIGIBLE")
            else:
                ineligible_programs.append(program)
                reason = "Credit score" if status == "INELIGIBLE" else "Insufficient funds"
                qualification_report.append(f" {program.upper()}: NOT ELIGIBLE ({reason})")
        
        # Overall Qualification Assessment
        qualification_report.append(f"\n📊 OVERALL ASSESSMENT:")
        
        total_issues = len(credit_issues) + len(income_issues) + len(asset_issues)
        total_warnings = len(credit_warnings) + len(income_warnings) + len(asset_warnings)
        
        if total_issues == 0 and eligible_programs:
            overall_status = "QUALIFIED"
            status_icon = ""
            recommendation = "Proceed with loan processing"
        elif total_issues <= 1 and eligible_programs:
            overall_status = "CONDITIONALLY QUALIFIED"
            status_icon = "⚠️"
            recommendation = "Proceed with conditions or manual underwriting"
        elif eligible_programs and total_issues <= 2:
            overall_status = "MARGINAL"
            status_icon = "⚠️"
            recommendation = "Manual underwriting required"
        else:
            overall_status = "NOT QUALIFIED"
            status_icon = ""
            recommendation = "Does not meet minimum requirements"
        
        qualification_report.append(f"{status_icon} Status: {overall_status}")
        qualification_report.append(f"Eligible Programs: {len(eligible_programs)}")
        qualification_report.append(f"Critical Issues: {total_issues}")
        qualification_report.append(f"Warnings: {total_warnings}")
        qualification_report.append(f"Recommendation: {recommendation}")
        
        # Issues Summary
        if credit_issues or income_issues or asset_issues:
            qualification_report.append(f"\n CRITICAL ISSUES:")
            for issue in credit_issues + income_issues + asset_issues:
                qualification_report.append(f"  • {issue}")
        
        if credit_warnings or income_warnings or asset_warnings:
            qualification_report.append(f"\n⚠️ WARNINGS:")
            for warning in credit_warnings + income_warnings + asset_warnings:
                qualification_report.append(f"  • {warning}")
        
        # Workflow Routing Recommendation
        qualification_report.append(f"\n🔄 ROUTING RECOMMENDATION:")
        
        if overall_status == "NOT QUALIFIED":
            qualification_report.append("1. Route to MortgageAdvisorAgent for improvement guidance")
            qualification_report.append("2. Provide qualification improvement strategies")
            qualification_report.append("3. Set follow-up timeline for re-qualification")
        elif first_time_buyer or credit_score < 650:
            qualification_report.append("1. Route to MortgageAdvisorAgent for program guidance")
            qualification_report.append("2. Proceed to DocumentAgent for verification")
            qualification_report.append("3. Continue standard processing workflow")
        elif overall_status in ["QUALIFIED", "CONDITIONALLY QUALIFIED"]:
            qualification_report.append("1. Proceed directly to DocumentAgent")
            qualification_report.append("2. Continue to AppraisalAgent for property evaluation")
            qualification_report.append("3. Route to UnderwritingAgent for final approval")
        else:
            qualification_report.append("1. Manual underwriting review required")
            qualification_report.append("2. Senior underwriter consultation recommended")
            qualification_report.append("3. Additional documentation may be required")
        
        # Best Program Recommendation
        if eligible_programs:
            qualification_report.append(f"\n⭐ RECOMMENDED LOAN PROGRAM:")
            
            # Prioritize programs based on borrower profile
            if military_service and "va" in eligible_programs:
                best_program = "VA"
                reason = "No down payment required, competitive rates"
            elif rural_property and "usda" in eligible_programs:
                best_program = "USDA"
                reason = "No down payment, rural property financing"
            elif first_time_buyer and "fha" in eligible_programs:
                best_program = "FHA"
                reason = "Low down payment, first-time buyer friendly"
            elif "conventional" in eligible_programs:
                best_program = "Conventional"
                reason = "Most flexible terms and competitive rates"
            else:
                best_program = eligible_programs[0].upper()
                reason = "Best available option based on qualification"
            
            qualification_report.append(f"Program: {best_program}")
            qualification_report.append(f"Reason: {reason}")
        
        return "\n".join(qualification_report)
        
    except Exception as e:
        logger.error(f"Error during initial qualification: {e}")
        return f" Error during initial qualification: {str(e)}"


def validate_tool() -> bool:
    """Validate that the perform_initial_qualification tool works correctly."""
    try:
        # Test with sample natural language data
        result = perform_initial_qualification.invoke({
            "borrower_info": "Credit score is 720, monthly income $8,000, monthly debts $1,200, have $100,000 in savings, employed 4 years W2, loan amount $400,000, property value $500,000, down payment $100,000"
        })
        return "INITIAL QUALIFICATION ASSESSMENT" in result and "OVERALL ASSESSMENT" in result
    except Exception as e:
        print(f"Initial qualification tool validation failed: {e}")
        return False
