"""
Initial Qualification Assessment Tool

This tool performs initial qualification and pre-screening
based on Neo4j application intake rules.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
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


class InitialQualificationRequest(BaseModel):
    """Initial qualification assessment request parameters."""
    application_id: str = Field(..., description="Application ID")
    credit_score: int = Field(..., description="Credit score")
    monthly_gross_income: float = Field(..., description="Monthly gross income")
    monthly_debts: float = Field(..., description="Total monthly debt payments")
    liquid_assets: float = Field(..., description="Available liquid assets")
    employment_years: float = Field(..., description="Years with current employer")
    employment_type: str = Field(..., description="Employment type (w2, self_employed, contract)")
    loan_amount: float = Field(..., description="Requested loan amount")
    property_value: float = Field(..., description="Property value")
    down_payment: float = Field(..., description="Down payment amount")
    property_type: str = Field(..., description="Property type")
    occupancy_type: str = Field(..., description="Occupancy type")
    loan_purpose: str = Field(..., description="Loan purpose")
    first_time_buyer: bool = Field(default=False, description="First-time home buyer")
    military_service: bool = Field(default=False, description="Military service")
    rural_property: bool = Field(default=False, description="Rural property location")
    
    # Credit history details
    bankruptcy_history: bool = Field(default=False, description="Bankruptcy history")
    foreclosure_history: bool = Field(default=False, description="Foreclosure history")
    collections_amount: float = Field(default=0, description="Outstanding collections amount")
    late_payments_12_months: int = Field(default=0, description="Late payments in last 12 months")


@tool(args_schema=InitialQualificationRequest)
def perform_initial_qualification(
    application_id: str,
    credit_score: int,
    monthly_gross_income: float,
    monthly_debts: float,
    liquid_assets: float,
    employment_years: float,
    employment_type: str,
    loan_amount: float,
    property_value: float,
    down_payment: float,
    property_type: str,
    occupancy_type: str,
    loan_purpose: str,
    first_time_buyer: bool = False,
    military_service: bool = False,
    rural_property: bool = False,
    bankruptcy_history: bool = False,
    foreclosure_history: bool = False,
    collections_amount: float = 0,
    late_payments_12_months: int = 0
) -> str:
    """
    Perform initial qualification assessment using Neo4j application intake rules.
    
    This tool evaluates initial qualification across multiple loan programs
    and provides routing recommendations for the application workflow.
    """
    
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
        # Test with sample data
        result = perform_initial_qualification.invoke({
            "application_id": "APP_20240101_123456_SMI",
            "credit_score": 720,
            "monthly_gross_income": 8000.0,
            "monthly_debts": 1200.0,
            "liquid_assets": 100000.0,
            "employment_years": 4.0,
            "employment_type": "w2",
            "loan_amount": 400000.0,
            "property_value": 500000.0,
            "down_payment": 100000.0,
            "property_type": "single_family_detached",
            "occupancy_type": "primary_residence",
            "loan_purpose": "purchase",
            "first_time_buyer": False,
            "military_service": False,
            "rural_property": False,
            "bankruptcy_history": False,
            "foreclosure_history": False,
            "collections_amount": 0,
            "late_payments_12_months": 0
        })
        return "INITIAL QUALIFICATION ASSESSMENT" in result and "OVERALL ASSESSMENT" in result
    except Exception as e:
        print(f"Initial qualification tool validation failed: {e}")
        return False
