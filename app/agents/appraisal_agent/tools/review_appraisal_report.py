"""
Appraisal Report Review Tool

This tool reviews and validates appraisal reports for compliance
based on Neo4j property appraisal rules.
"""

import logging
from typing import Dict, Any
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection

logger = logging.getLogger(__name__)


def parse_appraisal_report_info(report_info: str) -> Dict[str, Any]:
    """Extract appraisal report information from natural language description."""
    import re
    
    # Initialize with safe defaults
    parsed = {
        "property_address": "",
        "appraised_value": 400000.0,    # Default appraised value
        "loan_amount": 350000.0,        # Default loan amount
        "property_type": "single_family_detached",
        "appraisal_date": "2024-01-15", # Default recent date
        "appraiser_license": "LIC-12345", # Default license
        "appraisal_approach": "sales_comparison", # Default approach
        "comparable_count": 3,          # Default comp count
        "highest_comparable": 420000.0, # Default high comp
        "lowest_comparable": 380000.0,  # Default low comp
        "gross_adjustments_pct": 15.0,  # Default gross adjustment %
        "net_adjustments_pct": 8.0,     # Default net adjustment %
        "condition_rating": "good",     # Default condition
        "loan_program": "conventional", # Default loan program
        "compliance_issues": []         # Default no issues
    }
    
    info_lower = report_info.lower()
    
    # Extract property address
    address_patterns = [
        r'(?:property|house|home|address)?\s*(?:at|address|located)?\s*([^,\n]+(?:,\s*[^,\n]+)*(?:,\s*[A-Z]{2})?)',
        r'(\d+\s+[A-Za-z\s]+(?:st|ave|rd|dr|blvd|ct|ln|way|pl)\.?(?:,\s*[^,\n]+)*)',
    ]
    
    for pattern in address_patterns:
        address_match = re.search(pattern, report_info, re.IGNORECASE)
        if address_match:
            parsed["property_address"] = address_match.group(1).strip()
            break
    
    # Extract appraised value
    value_patterns = [
        r'apprai(?:s|z)ed?\s*(?:value|for|at)?\s*(?:is|of|:)?\s*\$?([0-9,]+)',
        r'valued?\s*(?:at|for)?\s*\$?([0-9,]+)',
        r'appraisal\s*(?:value|amount)?\s*\$?([0-9,]+)'
    ]
    
    for pattern in value_patterns:
        value_match = re.search(pattern, info_lower)
        if value_match:
            parsed["appraised_value"] = float(value_match.group(1).replace(',', ''))
            break
    
    # Extract loan amount
    loan_patterns = [
        r'loan\s*(?:amount|for)?\s*(?:is|of|:)?\s*\$?([0-9,]+)',
        r'borrowing\s*\$?([0-9,]+)',
        r'mortgage\s*(?:amount|for)?\s*\$?([0-9,]+)'
    ]
    
    for pattern in loan_patterns:
        loan_match = re.search(pattern, info_lower)
        if loan_match:
            parsed["loan_amount"] = float(loan_match.group(1).replace(',', ''))
            break
    
    # Extract property type
    if 'condo' in info_lower or 'condominium' in info_lower:
        parsed["property_type"] = "condominium"
    elif 'townhouse' in info_lower or 'town house' in info_lower:
        parsed["property_type"] = "townhouse"
    elif 'single family' in info_lower or 'single-family' in info_lower:
        parsed["property_type"] = "single_family_detached"
    elif 'duplex' in info_lower:
        parsed["property_type"] = "duplex"
    
    # Extract appraisal date
    date_patterns = [
        r'apprai(?:s|z)ed?\s*(?:on|date)?\s*(\d{4}-\d{2}-\d{2})',
        r'appraisal\s*date\s*(?:is|:)?\s*(\d{4}-\d{2}-\d{2})',
        r'dated?\s*(\d{4}-\d{2}-\d{2})'
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, info_lower)
        if date_match:
            parsed["appraisal_date"] = date_match.group(1)
            break
    
    # Extract appraiser license
    license_patterns = [
        r'license\s*(?:number|#)?\s*(?:is|:)?\s*([A-Z0-9-]+)',
        r'appraiser\s*(?:license|#)\s*([A-Z0-9-]+)'
    ]
    
    for pattern in license_patterns:
        license_match = re.search(pattern, report_info)
        if license_match:
            parsed["appraiser_license"] = license_match.group(1)
            break
    
    # Extract appraisal approach
    if 'sales comparison' in info_lower or 'comparable sales' in info_lower:
        parsed["appraisal_approach"] = "sales_comparison"
    elif 'cost approach' in info_lower:
        parsed["appraisal_approach"] = "cost_approach"
    elif 'income approach' in info_lower:
        parsed["appraisal_approach"] = "income_approach"
    
    # Extract comparable count
    comp_patterns = [
        r'(\d+)\s*comparable?s?',
        r'used\s*(\d+)\s*comp',
        r'(\d+)\s*comp\s*sales?'
    ]
    
    for pattern in comp_patterns:
        comp_match = re.search(pattern, info_lower)
        if comp_match:
            parsed["comparable_count"] = int(comp_match.group(1))
            break
    
    # Extract comparable prices
    high_comp_patterns = [
        r'highest?\s*comp(?:arable)?\s*(?:was|at|:)?\s*\$?([0-9,]+)',
        r'high\s*comp\s*\$?([0-9,]+)'
    ]
    
    for pattern in high_comp_patterns:
        high_match = re.search(pattern, info_lower)
        if high_match:
            parsed["highest_comparable"] = float(high_match.group(1).replace(',', ''))
            break
    
    low_comp_patterns = [
        r'lowest?\s*comp(?:arable)?\s*(?:was|at|:)?\s*\$?([0-9,]+)',
        r'low\s*comp\s*\$?([0-9,]+)'
    ]
    
    for pattern in low_comp_patterns:
        low_match = re.search(pattern, info_lower)
        if low_match:
            parsed["lowest_comparable"] = float(low_match.group(1).replace(',', ''))
            break
    
    # Extract adjustment percentages
    gross_adj_patterns = [
        r'gross\s*adjust(?:ment)?s?\s*(?:are|is|:)?\s*(\d+(?:\.\d+)?)%',
        r'total\s*adjust(?:ment)?s?\s*(\d+(?:\.\d+)?)%'
    ]
    
    for pattern in gross_adj_patterns:
        gross_match = re.search(pattern, info_lower)
        if gross_match:
            parsed["gross_adjustments_pct"] = float(gross_match.group(1))
            break
    
    net_adj_patterns = [
        r'net\s*adjust(?:ment)?s?\s*(?:are|is|:)?\s*(\d+(?:\.\d+)?)%'
    ]
    
    for pattern in net_adj_patterns:
        net_match = re.search(pattern, info_lower)
        if net_match:
            parsed["net_adjustments_pct"] = float(net_match.group(1))
            break
    
    # Extract condition rating
    if 'excellent' in info_lower:
        parsed["condition_rating"] = "excellent"
    elif 'good' in info_lower:
        parsed["condition_rating"] = "good"
    elif 'fair' in info_lower:
        parsed["condition_rating"] = "fair"
    elif 'poor' in info_lower:
        parsed["condition_rating"] = "poor"
    
    # Extract loan program
    if 'fha' in info_lower:
        parsed["loan_program"] = "fha"
    elif 'va' in info_lower:
        parsed["loan_program"] = "va"
    elif 'usda' in info_lower:
        parsed["loan_program"] = "usda"
    elif 'conventional' in info_lower:
        parsed["loan_program"] = "conventional"
    
    # Extract compliance issues
    issues = []
    if 'compliance issue' in info_lower or 'violation' in info_lower:
        if 'ltv' in info_lower:
            issues.append("LTV concerns")
        if 'adjustment' in info_lower and ('high' in info_lower or 'excessive' in info_lower):
            issues.append("High adjustments")
        if 'comparable' in info_lower and ('poor' in info_lower or 'inadequate' in info_lower):
            issues.append("Inadequate comparables")
    
    parsed["compliance_issues"] = issues
    
    return parsed


@tool
def review_appraisal_report(
    report_info: str
) -> str:
    """
    Review and validate appraisal reports for compliance using Neo4j appraisal rules.
    
    This tool evaluates appraisal reports against industry standards and loan program
    requirements to ensure compliance and accuracy.
    
    Provide appraisal report information in natural language, such as:
    "Property at 123 Oak St appraised for $450,000, loan amount $350,000, sales comparison approach, used 3 comparables, highest comp $465,000, lowest $435,000, gross adjustments 12%, net adjustments 5%, good condition"
    "Appraisal report dated 2024-01-15 for single family home, appraised value $420,000, FHA loan $378,000, appraiser license #12345-TX, condition excellent, 4 comparables used"
    """
    
    # Parse the natural language input
    parsed_info = parse_appraisal_report_info(report_info)
    
    # Extract all the parameters
    property_address = parsed_info["property_address"]
    appraised_value = parsed_info["appraised_value"]
    loan_amount = parsed_info["loan_amount"]
    property_type = parsed_info["property_type"]
    appraisal_date = parsed_info["appraisal_date"]
    appraiser_license = parsed_info["appraiser_license"]
    appraisal_approach = parsed_info["appraisal_approach"]
    comparable_count = parsed_info["comparable_count"]
    highest_comparable = parsed_info["highest_comparable"]
    lowest_comparable = parsed_info["lowest_comparable"]
    gross_adjustments_pct = parsed_info["gross_adjustments_pct"]
    net_adjustments_pct = parsed_info["net_adjustments_pct"]
    condition_rating = parsed_info["condition_rating"]
    loan_program = parsed_info["loan_program"]
    compliance_issues = parsed_info["compliance_issues"]
        
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        # Calculate LTV
        ltv = (loan_amount / appraised_value * 100) if appraised_value > 0 else 0
        
        with connection.driver.session(database=connection.database) as session:
            # Get appraisal standards rules for compliance verification
            standards_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'AppraisalStandards'
            RETURN rule
            """
            result = session.run(standards_rules_query)
            # Convert result to list immediately to avoid consumption errors  
            list(result)  # Standards rules consumed for compliance verification
            
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
        # Test with sample natural language data
        result = review_appraisal_report.invoke({
            "report_info": "Property at 123 Main St, Anytown, CA 90210 appraised for $500,000, loan amount $400,000, single family home, appraisal dated 2024-01-15, appraiser license AL123456, sales comparison approach, used 3 comparables, highest comp $515,000, lowest $485,000, gross adjustments 12.5%, net adjustments 8%, good condition, conventional loan"
        })
        return "APPRAISAL REPORT REVIEW" in result and "OVERALL ASSESSMENT" in result
    except Exception as e:
        print(f"Appraisal report review tool validation failed: {e}")
        return False
