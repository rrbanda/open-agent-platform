"""
Application Completeness Check Tool

This tool verifies application completeness against requirements
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


class ApplicationCompletenessRequest(BaseModel):
    """Application completeness check request parameters."""
    application_id: str = Field(default="TEMP_CHECK", description="Application ID to check")
    loan_purpose: str = Field(default="purchase", description="Loan purpose (purchase, refinance, etc.)")
    employment_type: str = Field(default="w2", description="Employment type (w2, self_employed, contract)")
    has_co_borrower: bool = Field(default=False, description="Has co-borrower")
    property_type: str = Field(default="single_family_detached", description="Property type")
    occupancy_type: str = Field(default="primary_residence", description="Occupancy type")
    
    # Field status (True = provided, False = missing)
    personal_info_complete: bool = Field(default=True, description="Personal information complete")
    address_info_complete: bool = Field(default=True, description="Address information complete")
    employment_info_complete: bool = Field(default=True, description="Employment information complete")
    income_documentation: bool = Field(default=False, description="Income documentation provided")
    asset_documentation: bool = Field(default=False, description="Asset documentation provided")
    debt_documentation: bool = Field(default=False, description="Debt documentation provided")
    property_documentation: bool = Field(default=False, description="Property documentation provided")
    insurance_documentation: bool = Field(default=False, description="Insurance documentation provided")
    
    # Additional documentation flags
    tax_returns_provided: bool = Field(default=False, description="Tax returns provided")
    bank_statements_provided: bool = Field(default=False, description="Bank statements provided")
    paystubs_provided: bool = Field(default=False, description="Pay stubs provided")
    w2_forms_provided: bool = Field(default=False, description="W2 forms provided")
    credit_report_authorized: bool = Field(default=False, description="Credit report authorization signed")


@tool(args_schema=ApplicationCompletenessRequest)
def check_application_completeness(
    application_id: str = "TEMP_CHECK",
    loan_purpose: str = "purchase", 
    employment_type: str = "w2",
    has_co_borrower: bool = False,
    property_type: str = "single_family_detached",
    occupancy_type: str = "primary_residence",
    personal_info_complete: bool = True,
    address_info_complete: bool = True,
    employment_info_complete: bool = True,
    income_documentation: bool = False,
    asset_documentation: bool = False,
    debt_documentation: bool = False,
    property_documentation: bool = False,
    insurance_documentation: bool = False,
    tax_returns_provided: bool = False,
    bank_statements_provided: bool = False,
    paystubs_provided: bool = False,
    w2_forms_provided: bool = False,
    credit_report_authorized: bool = False
) -> str:
    """
    Check application completeness against requirements using Neo4j application intake rules.
    
    This tool verifies that all required documentation and information has been
    provided based on loan type, employment type, and property characteristics.
    """
    
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get completeness validation rules
            completeness_query = """
            MATCH (rule:ApplicationIntakeRule)
            WHERE rule.category = 'ValidationRules' AND rule.rule_type = 'completeness_validation'
            RETURN rule
            """
            result = session.run(completeness_query)
            completeness_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
            
            # Get application requirements
            requirements_query = """
            MATCH (rule:ApplicationIntakeRule)
            WHERE rule.category = 'ApplicationRequirements'
            RETURN rule
            """
            result = session.run(requirements_query)
            requirements_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
        
        # Generate completeness report
        completeness_report = []
        completeness_report.append("APPLICATION COMPLETENESS ANALYSIS")
        completeness_report.append("=" * 50)
        
        # Application Information
        completeness_report.append(f"\n📋 APPLICATION DETAILS:")
        completeness_report.append(f"Application ID: {application_id}")
        completeness_report.append(f"Loan Purpose: {loan_purpose.replace('_', ' ').title()}")
        completeness_report.append(f"Employment Type: {employment_type.replace('_', ' ').title()}")
        completeness_report.append(f"Property Type: {property_type.replace('_', ' ').title()}")
        completeness_report.append(f"Occupancy: {occupancy_type.replace('_', ' ').title()}")
        if has_co_borrower:
            completeness_report.append(" Co-Borrower Application")
        
        # Basic Information Completeness
        completeness_report.append(f"\n📝 BASIC INFORMATION COMPLETENESS:")
        
        basic_sections = [
            ("Personal Information", personal_info_complete),
            ("Address Information", address_info_complete),
            ("Employment Information", employment_info_complete)
        ]
        
        basic_complete_count = 0
        for section, is_complete in basic_sections:
            status = "" if is_complete else ""
            completeness_report.append(f"  {status} {section}")
            if is_complete:
                basic_complete_count += 1
        
        basic_completion_rate = (basic_complete_count / len(basic_sections)) * 100
        completeness_report.append(f"📊 Basic Information: {basic_completion_rate:.0f}% complete")
        
        # Documentation Requirements Analysis
        completeness_report.append(f"\n📄 DOCUMENTATION REQUIREMENTS:")
        
        missing_docs = []
        provided_docs = []
        conditional_docs = []
        
        # Get completeness rule
        completeness_rule = completeness_rules[0] if completeness_rules else {}
        conditional_reqs = completeness_rule.get('conditional_requirements', {})
        
        # Standard documentation requirements
        standard_docs = [
            ("Income Documentation", income_documentation, "Required for all loans"),
            ("Asset Documentation", asset_documentation, "Required for down payment verification"),
            ("Credit Report Authorization", credit_report_authorized, "Required for credit analysis"),
            ("Property Documentation", property_documentation, "Required for property verification")
        ]
        
        for doc_name, is_provided, description in standard_docs:
            if is_provided:
                provided_docs.append((doc_name, description))
                completeness_report.append(f"   {doc_name}")
            else:
                missing_docs.append((doc_name, description))
                completeness_report.append(f"   {doc_name} - {description}")
        
        # Employment-specific requirements
        if employment_type == "self_employed":
            self_employed_docs = [
                ("Tax Returns", tax_returns_provided, "2 years tax returns required for self-employed"),
                ("Profit & Loss Statements", debt_documentation, "Current year P&L required")
            ]
            
            completeness_report.append(f"\n💼 SELF-EMPLOYED REQUIREMENTS:")
            for doc_name, is_provided, description in self_employed_docs:
                if is_provided:
                    provided_docs.append((doc_name, description))
                    completeness_report.append(f"   {doc_name}")
                else:
                    missing_docs.append((doc_name, description))
                    completeness_report.append(f"   {doc_name} - {description}")
        
        elif employment_type == "w2":
            w2_docs = [
                ("Pay Stubs", paystubs_provided, "Recent pay stubs (30 days)"),
                ("W2 Forms", w2_forms_provided, "2 years W2 forms")
            ]
            
            completeness_report.append(f"\n💼 W2 EMPLOYEE REQUIREMENTS:")
            for doc_name, is_provided, description in w2_docs:
                if is_provided:
                    provided_docs.append((doc_name, description))
                    completeness_report.append(f"   {doc_name}")
                else:
                    missing_docs.append((doc_name, description))
                    completeness_report.append(f"   {doc_name} - {description}")
        
        # Asset documentation requirements
        completeness_report.append(f"\n💰 ASSET DOCUMENTATION:")
        asset_docs = [
            ("Bank Statements", bank_statements_provided, "2 months recent statements")
        ]
        
        for doc_name, is_provided, description in asset_docs:
            if is_provided:
                provided_docs.append((doc_name, description))
                completeness_report.append(f"   {doc_name}")
            else:
                missing_docs.append((doc_name, description))
                completeness_report.append(f"   {doc_name} - {description}")
        
        # Co-borrower requirements
        if has_co_borrower:
            completeness_report.append(f"\n👥 CO-BORROWER REQUIREMENTS:")
            completeness_report.append("   Co-Borrower Income Documentation - Required")
            completeness_report.append("   Co-Borrower Asset Documentation - Required")
            completeness_report.append("   Co-Borrower Employment Verification - Required")
            missing_docs.extend([
                ("Co-Borrower Income Documentation", "Required for qualification"),
                ("Co-Borrower Asset Documentation", "Required for down payment"),
                ("Co-Borrower Employment Verification", "Required for income stability")
            ])
        
        # Loan Purpose Specific Requirements
        loan_purpose_rule = next((rule for rule in requirements_rules if rule.get('rule_type') == 'loan_purpose_validation'), {})
        purpose_requirements = loan_purpose_rule.get('purpose_requirements', {})
        
        if loan_purpose in purpose_requirements:
            specific_reqs = purpose_requirements[loan_purpose]
            completeness_report.append(f"\n🎯 {loan_purpose.upper().replace('_', ' ')} SPECIFIC REQUIREMENTS:")
            
            for req in specific_reqs:
                req_name = req.replace('_', ' ').title()
                # Assume not provided for demonstration
                completeness_report.append(f"   {req_name} - Required for {loan_purpose}")
                missing_docs.append((req_name, f"Required for {loan_purpose}"))
        
        # Property Type Specific Requirements
        if property_type == "condominium":
            completeness_report.append(f"\n🏢 CONDOMINIUM SPECIFIC REQUIREMENTS:")
            condo_docs = ["HOA Documents", "Condo Certification", "HOA Budget"]
            for doc in condo_docs:
                completeness_report.append(f"   {doc} - Required for condominium financing")
                missing_docs.append((doc, "Required for condominium financing"))
        
        # Occupancy Type Requirements
        if occupancy_type == "investment_property":
            completeness_report.append(f"\n🏠 INVESTMENT PROPERTY REQUIREMENTS:")
            investment_docs = ["Rental Income Documentation", "Property Management Agreement"]
            for doc in investment_docs:
                completeness_report.append(f"   {doc} - Required for investment property")
                missing_docs.append((doc, "Required for investment property"))
        
        # Completeness Summary
        completeness_report.append(f"\n📊 COMPLETENESS SUMMARY:")
        
        total_requirements = len(provided_docs) + len(missing_docs)
        provided_count = len(provided_docs)
        
        if total_requirements > 0:
            completion_percentage = (provided_count / total_requirements) * 100
            completeness_report.append(f"Overall Completion: {completion_percentage:.1f}%")
            completeness_report.append(f"Documents Provided: {provided_count}")
            completeness_report.append(f"Documents Missing: {len(missing_docs)}")
        
        # Get minimum completion threshold
        min_completion = completeness_rule.get('required_completion_percentage', 0.85) * 100
        
        # Status Assessment
        completeness_report.append(f"\n🎯 STATUS ASSESSMENT:")
        
        if not missing_docs and basic_completion_rate == 100:
            status = "COMPLETE"
            status_icon = ""
            next_action = "Ready for processing workflow"
        elif completion_percentage >= min_completion and basic_completion_rate == 100:
            status = "SUBSTANTIALLY COMPLETE"
            status_icon = "⚠️"
            next_action = "Can proceed with conditional approval"
        else:
            status = "INCOMPLETE"
            status_icon = ""
            next_action = "Requires additional documentation"
        
        completeness_report.append(f"{status_icon} Application Status: {status}")
        completeness_report.append(f"Required Completion: {min_completion:.0f}%")
        completeness_report.append(f"Current Completion: {completion_percentage:.1f}%")
        completeness_report.append(f"Next Action: {next_action}")
        
        # Missing Documents List
        if missing_docs:
            completeness_report.append(f"\n📋 MISSING DOCUMENTATION:")
            for i, (doc_name, description) in enumerate(missing_docs, 1):
                completeness_report.append(f"  {i}. {doc_name}")
                completeness_report.append(f"     → {description}")
        
        # Provided Documents List
        if provided_docs:
            completeness_report.append(f"\n PROVIDED DOCUMENTATION:")
            for i, (doc_name, description) in enumerate(provided_docs, 1):
                completeness_report.append(f"  {i}. {doc_name}")
        
        # Recommendations
        completeness_report.append(f"\n💡 RECOMMENDATIONS:")
        
        if status == "COMPLETE":
            completeness_report.append("1. Proceed immediately to document verification")
            completeness_report.append("2. Initiate credit analysis and underwriting process")
        elif status == "SUBSTANTIALLY COMPLETE":
            completeness_report.append("1. Proceed with initial processing")
            completeness_report.append("2. Request missing documents during underwriting")
            completeness_report.append("3. Set conditional approval pending documentation")
        else:
            completeness_report.append("1. Contact applicant for missing documentation")
            completeness_report.append("2. Provide clear list of required documents")
            completeness_report.append("3. Set follow-up timeline for completion")
            if has_co_borrower:
                completeness_report.append("4. Ensure co-borrower documentation is complete")
        
        return "\n".join(completeness_report)
        
    except Exception as e:
        logger.error(f"Error during completeness check: {e}")
        return f" Error during completeness check: {str(e)}"


def validate_tool() -> bool:
    """Validate that the check_application_completeness tool works correctly."""
    try:
        # Test with sample data
        result = check_application_completeness.invoke({
            "application_id": "APP_20240101_123456_SMI",
            "loan_purpose": "purchase",
            "employment_type": "w2",
            "has_co_borrower": False,
            "property_type": "single_family_detached",
            "occupancy_type": "primary_residence",
            "personal_info_complete": True,
            "address_info_complete": True,
            "employment_info_complete": True,
            "income_documentation": True,
            "asset_documentation": True,
            "debt_documentation": False,
            "property_documentation": False,
            "insurance_documentation": False,
            "tax_returns_provided": False,
            "bank_statements_provided": True,
            "paystubs_provided": True,
            "w2_forms_provided": True,
            "credit_report_authorized": True
        })
        return "APPLICATION COMPLETENESS ANALYSIS" in result and "STATUS ASSESSMENT" in result
    except Exception as e:
        print(f"Application completeness tool validation failed: {e}")
        return False
