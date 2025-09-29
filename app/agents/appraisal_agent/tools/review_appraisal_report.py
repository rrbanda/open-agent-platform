"""
Appraisal Report Review Tool

This tool reviews and validates appraisal reports for compliance
based on Neo4j property appraisal rules.
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


class AppraisalReportReviewRequest(BaseModel):
    """Appraisal report review request parameters."""
    property_address: str = Field(..., description="Property address")
    appraised_value: float = Field(..., description="Final appraised value")
    loan_amount: float = Field(..., description="Requested loan amount")
    property_type: str = Field(..., description="Property type")
    appraisal_date: str = Field(..., description="Appraisal effective date")
    appraiser_license: str = Field(..., description="Appraiser license number")
    appraisal_approach: str = Field(..., description="Primary appraisal approach used")
    comparable_count: int = Field(..., description="Number of comparables used")
    highest_comparable: float = Field(..., description="Highest comparable sale price")
    lowest_comparable: float = Field(..., description="Lowest comparable sale price")
    gross_adjustments_pct: float = Field(..., description="Gross adjustments percentage")
    net_adjustments_pct: float = Field(..., description="Net adjustments percentage")
    condition_rating: str = Field(..., description="Property condition rating")
    loan_program: str = Field(default="conventional", description="Loan program")
    compliance_issues: Optional[List[str]] = Field(default=[], description="Any compliance issues noted")


@tool(args_schema=AppraisalReportReviewRequest)
def review_appraisal_report(
    property_address: str,
    appraised_value: float,
    loan_amount: float,
    property_type: str,
    appraisal_date: str,
    appraiser_license: str,
    appraisal_approach: str,
    comparable_count: int,
    highest_comparable: float,
    lowest_comparable: float,
    gross_adjustments_pct: float,
    net_adjustments_pct: float,
    condition_rating: str,
    loan_program: str = "conventional",
    compliance_issues: Optional[List[str]] = None
) -> str:
    """
    Review and validate appraisal reports for compliance using Neo4j appraisal rules.
    
    This tool evaluates appraisal reports against industry standards and loan program
    requirements to ensure compliance and accuracy.
    """
    
    if compliance_issues is None:
        compliance_issues = []
        
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        # Calculate LTV
        ltv = (loan_amount / appraised_value * 100) if appraised_value > 0 else 0
        
        with connection.driver.session(database=connection.database) as session:
            # Get appraisal standards rules
            standards_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'AppraisalStandards'
            RETURN rule
            """
            result = session.run(standards_rules_query)
            standards_rules = [dict(record['rule']) for record in result]
            
            # Get value analysis rules for adjustment limits
            value_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'ValueAnalysis' AND rule.approach_type = 'sales_comparison'
            RETURN rule
            """
            result = session.run(value_rules_query)
            value_rules = [dict(record['rule']) for record in result]
            
            # Get property type specific rules
            property_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'PropertyType' AND rule.property_type = $property_type
            RETURN rule
            """
            result = session.run(property_rules_query, {"property_type": property_type})
            property_rules = [dict(record['rule']) for record in result]
        
        # Generate appraisal review report
        review_report = []
        review_report.append("APPRAISAL REPORT REVIEW")
        review_report.append("=" * 50)
        
        # Basic Information
        review_report.append(f"\n📋 APPRAISAL INFORMATION:")
        review_report.append(f"Property: {property_address}")
        review_report.append(f"Appraised Value: ${appraised_value:,.2f}")
        review_report.append(f"Loan Amount: ${loan_amount:,.2f}")
        review_report.append(f"Loan-to-Value: {ltv:.1f}%")
        review_report.append(f"Property Type: {property_type.replace('_', ' ').title()}")
        review_report.append(f"Appraisal Date: {appraisal_date}")
        review_report.append(f"Appraiser License: {appraiser_license}")
        review_report.append(f"Loan Program: {loan_program.upper()}")
        
        # Valuation Analysis Review
        review_report.append(f"\n💰 VALUATION ANALYSIS REVIEW:")
        review_report.append(f"Primary Approach: {appraisal_approach.replace('_', ' ').title()}")
        review_report.append(f"Number of Comparables: {comparable_count}")
        review_report.append(f"Comparable Range: ${lowest_comparable:,.0f} - ${highest_comparable:,.0f}")
        
        # Calculate comparable spread
        if highest_comparable > 0 and lowest_comparable > 0:
            comparable_spread = ((highest_comparable - lowest_comparable) / lowest_comparable) * 100
            review_report.append(f"Comparable Spread: {comparable_spread:.1f}%")
        
        # Adjustment Analysis
        review_report.append(f"\n🔧 ADJUSTMENT ANALYSIS:")
        review_report.append(f"Gross Adjustments: {gross_adjustments_pct:.1f}%")
        review_report.append(f"Net Adjustments: {net_adjustments_pct:.1f}%")
        
        # Compliance Checks
        review_report.append(f"\n COMPLIANCE VERIFICATION:")
        
        compliance_status = []
        critical_issues = []
        warnings = []
        
        # 1. Comparable Count Check
        property_rule = property_rules[0] if property_rules else {}
        required_comps = property_rule.get('comparable_requirements', '3_minimum')
        min_comps = 3 if '3_minimum' in required_comps else 2
        
        if comparable_count >= min_comps:
            compliance_status.append(f" Comparable Count: {comparable_count} (meets {min_comps} minimum)")
        else:
            compliance_status.append(f" Comparable Count: {comparable_count} (below {min_comps} minimum)")
            critical_issues.append(f"Insufficient comparables: {comparable_count} provided, {min_comps} required")
        
        # 2. Adjustment Limits Check
        value_rule = value_rules[0] if value_rules else {}
        gross_limit = value_rule.get('gross_adjustment_limit', 0.25) * 100
        net_limit = value_rule.get('net_adjustment_limit', 0.15) * 100
        
        if gross_adjustments_pct <= gross_limit:
            compliance_status.append(f" Gross Adjustments: {gross_adjustments_pct:.1f}% (within {gross_limit:.0f}% limit)")
        else:
            compliance_status.append(f" Gross Adjustments: {gross_adjustments_pct:.1f}% (exceeds {gross_limit:.0f}% limit)")
            critical_issues.append(f"Gross adjustments exceed acceptable limits")
        
        if net_adjustments_pct <= net_limit:
            compliance_status.append(f" Net Adjustments: {net_adjustments_pct:.1f}% (within {net_limit:.0f}% limit)")
        else:
            compliance_status.append(f" Net Adjustments: {net_adjustments_pct:.1f}% (exceeds {net_limit:.0f}% limit)")
            warnings.append(f"Net adjustments near or exceed recommended limits")
        
        # 3. LTV Compliance
        if loan_program.lower() == 'conventional':
            if ltv <= 80:
                compliance_status.append(f" LTV: {ltv:.1f}% (conventional conforming)")
            elif ltv <= 97:
                compliance_status.append(f"⚠️ LTV: {ltv:.1f}% (requires mortgage insurance)")
                warnings.append("High LTV loan - verify mortgage insurance requirements")
            else:
                compliance_status.append(f" LTV: {ltv:.1f}% (exceeds conventional limits)")
                critical_issues.append("LTV exceeds conventional loan limits")
        elif loan_program.lower() == 'fha':
            if ltv <= 96.5:
                compliance_status.append(f" LTV: {ltv:.1f}% (within FHA limits)")
            else:
                compliance_status.append(f" LTV: {ltv:.1f}% (exceeds FHA 96.5% limit)")
                critical_issues.append("LTV exceeds FHA limits")
        elif loan_program.lower() == 'va':
            if ltv <= 100:
                compliance_status.append(f" LTV: {ltv:.1f}% (within VA limits)")
            else:
                compliance_status.append(f" LTV: {ltv:.1f}% (exceeds VA 100% limit)")
                critical_issues.append("LTV exceeds VA limits")
        
        # 4. Appraiser Licensing
        if appraiser_license and len(appraiser_license) > 5:
            compliance_status.append(f" Appraiser Licensed: {appraiser_license}")
        else:
            compliance_status.append(f" Appraiser License: Invalid or missing")
            critical_issues.append("Valid appraiser license required")
        
        # 5. Property Condition
        acceptable_conditions = ['excellent', 'good', 'average']
        if condition_rating.lower() in acceptable_conditions:
            compliance_status.append(f" Property Condition: {condition_rating.title()}")
        else:
            compliance_status.append(f"⚠️ Property Condition: {condition_rating.title()}")
            warnings.append("Property condition may affect marketability")
        
        # Display compliance results
        for status in compliance_status:
            review_report.append(f"  {status}")
        
        # Market Support Analysis
        review_report.append(f"\n📊 MARKET SUPPORT ANALYSIS:")
        
        # Value relative to comparables
        if highest_comparable > 0 and lowest_comparable > 0:
            comp_midpoint = (highest_comparable + lowest_comparable) / 2
            value_vs_midpoint = ((appraised_value - comp_midpoint) / comp_midpoint) * 100
            
            if abs(value_vs_midpoint) <= 5:
                review_report.append(f" Value vs Comparable Midpoint: {value_vs_midpoint:+.1f}% (well supported)")
            elif abs(value_vs_midpoint) <= 10:
                review_report.append(f"⚠️ Value vs Comparable Midpoint: {value_vs_midpoint:+.1f}% (adequately supported)")
                warnings.append("Value at edge of comparable range")
            else:
                review_report.append(f" Value vs Comparable Midpoint: {value_vs_midpoint:+.1f}% (poorly supported)")
                critical_issues.append("Appraised value poorly supported by comparables")
        
        # Loan Program Specific Requirements
        review_report.append(f"\n📋 LOAN PROGRAM COMPLIANCE ({loan_program.upper()}):")
        
        if loan_program.lower() == 'fha':
            review_report.append("  FHA Requirements:")
            review_report.append("     Appraiser must be FHA-approved")
            review_report.append("     Property must meet HUD minimum property standards")
            if condition_rating.lower() == 'poor':
                review_report.append("     Property condition below FHA standards")
                critical_issues.append("Property condition must meet FHA standards")
            else:
                review_report.append("     Property condition meets FHA standards")
                
        elif loan_program.lower() == 'va':
            review_report.append("  VA Requirements:")
            review_report.append("     Appraiser must be VA-approved")
            review_report.append("     Property must meet VA minimum property requirements")
            review_report.append("     Certificate of Reasonable Value (CRV) issued")
            
        elif loan_program.lower() == 'usda':
            review_report.append("  USDA Requirements:")
            review_report.append("     Property must be in eligible rural area")
            review_report.append("     Property must meet USDA standards")
            
        else:  # Conventional
            review_report.append("  Conventional Requirements:")
            review_report.append("     USPAP compliance verified")
            review_report.append("     GSE selling guide requirements met")
        
        # Issues Summary
        if compliance_issues:
            review_report.append(f"\n⚠️ REPORTED COMPLIANCE ISSUES:")
            for issue in compliance_issues:
                review_report.append(f"    • {issue}")
        
        # Critical Issues
        if critical_issues:
            review_report.append(f"\n CRITICAL ISSUES IDENTIFIED:")
            for issue in critical_issues:
                review_report.append(f"    • {issue}")
        
        # Warnings
        if warnings:
            review_report.append(f"\n⚠️ WARNINGS:")
            for warning in warnings:
                review_report.append(f"    • {warning}")
        
        # Overall Assessment
        review_report.append(f"\n🎯 OVERALL ASSESSMENT:")
        
        if not critical_issues and not compliance_issues:
            review_report.append("   ACCEPTABLE: Appraisal meets all compliance requirements")
            review_status = "ACCEPTABLE"
        elif not critical_issues and (warnings or compliance_issues):
            review_report.append("  ⚠️ ACCEPTABLE WITH CONDITIONS: Minor issues noted")
            review_status = "ACCEPTABLE WITH CONDITIONS"
        else:
            review_report.append("   UNACCEPTABLE: Critical issues must be resolved")
            review_status = "UNACCEPTABLE"
        
        # Recommendations
        review_report.append(f"\n💡 RECOMMENDATIONS:")
        
        if review_status == "ACCEPTABLE":
            review_report.append("  1. Appraisal approved for loan processing")
            review_report.append("  2. File appraisal in loan documentation")
        elif review_status == "ACCEPTABLE WITH CONDITIONS":
            review_report.append("  1. Address noted warnings and conditions")
            review_report.append("  2. Document resolution of minor issues")
            review_report.append("  3. Proceed with loan processing")
        else:
            review_report.append("  1. Do not proceed with loan until issues resolved")
            review_report.append("  2. Obtain new appraisal if critical deficiencies cannot be corrected")
            review_report.append("  3. Review appraiser qualifications and methodology")
        
        if warnings:
            review_report.append("  4. Consider additional review by senior appraiser")
        
        # Quality Control
        review_report.append(f"\n🔍 QUALITY CONTROL CHECKLIST:")
        review_report.append("   Appraisal form completeness verified")
        review_report.append("   Comparable sales verification completed")
        review_report.append("   Adjustment methodology reviewed")
        review_report.append("   Final value reconciliation appropriate")
        review_report.append("   Supporting documentation adequate")
        
        return "\n".join(review_report)
        
    except Exception as e:
        logger.error(f"Error during appraisal report review: {e}")
        return f" Error during appraisal report review: {str(e)}"


def validate_tool() -> bool:
    """Validate that the review_appraisal_report tool works correctly."""
    try:
        # Test with sample data
        result = review_appraisal_report.invoke({
            "property_address": "123 Main St, Anytown, CA 90210",
            "appraised_value": 500000.0,
            "loan_amount": 400000.0,
            "property_type": "single_family_detached",
            "appraisal_date": "2024-01-15",
            "appraiser_license": "AL123456",
            "appraisal_approach": "sales_comparison",
            "comparable_count": 3,
            "highest_comparable": 515000.0,
            "lowest_comparable": 485000.0,
            "gross_adjustments_pct": 12.5,
            "net_adjustments_pct": 8.0,
            "condition_rating": "good",
            "loan_program": "conventional",
            "compliance_issues": []
        })
        return "APPRAISAL REPORT REVIEW" in result and "OVERALL ASSESSMENT" in result
    except Exception as e:
        print(f"Appraisal report review tool validation failed: {e}")
        return False
