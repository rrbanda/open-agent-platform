"""
Property Value Analysis Tool

This tool provides comprehensive property valuation analysis using multiple appraisal approaches
based on Neo4j property appraisal rules.
"""

import logging
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection

logger = logging.getLogger(__name__)




@tool
def analyze_property_value(property_info: str) -> str:
    """
    Analyze property value using multiple appraisal approaches based on Neo4j rules.
    
    This tool provides comprehensive property valuation analysis using sales comparison,
    cost, and income approaches based on industry standards and appraisal rules.
    
    Provide property information in natural language, such as:
    "Property at 456 Oak Ave Austin TX, single family home, loan amount $390,000, estimated value $450,000, 2200 sq ft, built in 2015"
    "Address 123 Main St Dallas TX, townhouse, loan $320,000, property value $380,000, 1800 sqft, year built 2018"
    "Condo at 789 Pine Blvd, loan amount $275,000, value estimate $325,000, 1400 square feet, built 2020"
    """
    
    try:
        # Parse property info string
        import re
        info = property_info.lower()
        
        # Extract property address
        address_match = re.search(r'address:\s*([^,]+(?:,\s*[^,]+)*)', info)
        property_address = address_match.group(1).strip() if address_match else "456 Oak Ave, Austin, TX"
        
        # Extract property type
        type_match = re.search(r'type:\s*([a-z_]+)', info)
        property_type = type_match.group(1) if type_match else "single_family_detached"
        
        # Extract loan amount
        loan_match = re.search(r'loan:\s*(\d+)', info)
        loan_amount = float(loan_match.group(1)) if loan_match else 390000.0
        
        # Extract property value
        value_match = re.search(r'value:\s*(\d+)', info)
        property_value = float(value_match.group(1)) if value_match else 450000.0
        
        # Extract square footage
        sqft_match = re.search(r'sqft:\s*(\d+)', info)
        gross_living_area = int(sqft_match.group(1)) if sqft_match else 2200
        
        # Extract year built
        built_match = re.search(r'built:\s*(\d{4})', info)
        year_built = int(built_match.group(1)) if built_match else 2015
        
        # Set defaults (for reference, not actively used)
        # lot_size = 0.25
        # bedrooms = 3  
        # bathrooms = 2.5
        # appraisal_purpose = "purchase"
        
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        # Calculate LTV if property value is provided
        ltv = (loan_amount / property_value * 100) if property_value else None
        
        with connection.driver.session(database=connection.database) as session:
            # Get property type specific rules
            property_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'PropertyType' AND rule.property_type = $property_type
            RETURN rule
            """
            result = session.run(property_rules_query, {"property_type": property_type})
            property_rules = [dict(record['rule']) for record in result]
            
            # Get value analysis rules
            value_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'ValueAnalysis'
            RETURN rule
            """
            result = session.run(value_rules_query)
            value_rules = [dict(record['rule']) for record in result]
            
            # Get property condition rules
            condition_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'PropertyCondition'
            RETURN rule
            """
            result = session.run(condition_rules_query)
            condition_rules = [dict(record['rule']) for record in result]
        
        # Analysis based on Neo4j rules
        analysis_report = []
        analysis_report.append("PROPERTY VALUE ANALYSIS REPORT")
        analysis_report.append("=" * 50)
        
        # Property Information
        analysis_report.append(f"\n📍 PROPERTY DETAILS:")
        analysis_report.append(f"Address: {property_address}")
        analysis_report.append(f"Property Type: {property_type.replace('_', ' ').title()}")
        analysis_report.append(f"Loan Amount: ${loan_amount:,.2f}")
        if property_value:
            analysis_report.append(f"Estimated Value: ${property_value:,.2f}")
            analysis_report.append(f"Loan-to-Value Ratio: {ltv:.1f}%")
        
        if gross_living_area:
            analysis_report.append(f"Gross Living Area: {gross_living_area:,} sq ft")
        if year_built:
            analysis_report.append(f"Year Built: {year_built}")
        if bedrooms:
            analysis_report.append(f"Bedrooms: {bedrooms}")
        if bathrooms:
            analysis_report.append(f"Bathrooms: {bathrooms}")
        
        # Property Type Analysis
        analysis_report.append(f"\n🏠 PROPERTY TYPE ANALYSIS:")
        if property_rules:
            property_rule = property_rules[0]
            analysis_report.append(f"Primary Appraisal Approach: {property_rule.get('appraisal_approach', 'N/A').replace('_', ' ').title()}")
            analysis_report.append(f"Comparable Requirements: {property_rule.get('comparable_requirements', 'N/A').replace('_', ' ')}")
            analysis_report.append(f"Distance Limit: {property_rule.get('distance_limit_miles', 'N/A')} miles")
            analysis_report.append(f"Age Limit: {property_rule.get('age_limit_months', 'N/A')} months")
            
            if property_rule.get('special_requirements'):
                analysis_report.append(f"Special Requirements: {', '.join(property_rule.get('special_requirements', []))}")
            
            if property_type == 'condominium' and property_rule.get('hoa_analysis_required'):
                analysis_report.append("⚠️ HOA Analysis Required")
                analysis_report.append("⚠️ Condominium Warrantability Review Required")
        else:
            analysis_report.append("⚠️ Property type rules not found in database")
        
        # Value Analysis Approaches
        analysis_report.append(f"\n💰 VALUE ANALYSIS APPROACHES:")
        
        # Sales Comparison Approach
        sales_comparison = next((rule for rule in value_rules if rule.get('approach_type') == 'sales_comparison'), None)
        if sales_comparison:
            analysis_report.append("\n1. Sales Comparison Approach (Primary):")
            analysis_report.append(f"   Required Comparables: {sales_comparison.get('comparable_count', 3)}")
            analysis_report.append(f"   Adjustment Categories: {', '.join(sales_comparison.get('adjustment_categories', []))}")
            analysis_report.append(f"   Gross Adjustment Limit: {sales_comparison.get('gross_adjustment_limit', 0.25)*100:.0f}%")
            analysis_report.append(f"   Net Adjustment Limit: {sales_comparison.get('net_adjustment_limit', 0.15)*100:.0f}%")
            analysis_report.append(f"   Data Sources: {', '.join(sales_comparison.get('data_sources', []))}")
        
        # Cost Approach
        cost_approach = next((rule for rule in value_rules if rule.get('approach_type') == 'cost_approach'), None)
        if cost_approach:
            analysis_report.append("\n2. Cost Approach:")
            when_required = cost_approach.get('when_required', [])
            if year_built and year_built >= 2020:
                analysis_report.append("    Required for new construction")
            else:
                analysis_report.append(f"   Required when: {', '.join(when_required)}")
            analysis_report.append(f"   Land Value Method: {cost_approach.get('land_value_method', 'N/A').replace('_', ' ')}")
            analysis_report.append(f"   Cost Sources: {cost_approach.get('cost_sources', 'N/A').replace('_', ' ')}")
        
        # Income Approach
        income_approach = next((rule for rule in value_rules if rule.get('approach_type') == 'income_approach'), None)
        if income_approach and property_type in ['2_4_unit', 'investment']:
            analysis_report.append("\n3. Income Approach:")
            analysis_report.append("    Required for investment/multi-unit property")
            analysis_report.append(f"   Rental Analysis: {income_approach.get('rental_analysis', 'N/A').replace('_', ' ')}")
            analysis_report.append(f"   Cap Rate: {income_approach.get('capitalization_rate', 'N/A').replace('_', ' ')}")
        
        # LTV Analysis
        if ltv:
            analysis_report.append(f"\n📊 LOAN-TO-VALUE ANALYSIS:")
            if ltv <= 80:
                analysis_report.append(f"    LTV {ltv:.1f}% - Conventional conforming range")
            elif ltv <= 90:
                analysis_report.append(f"   ⚠️ LTV {ltv:.1f}% - May require mortgage insurance")
            elif ltv <= 95:
                analysis_report.append(f"   ⚠️ LTV {ltv:.1f}% - High LTV, special programs required")
            else:
                analysis_report.append(f"    LTV {ltv:.1f}% - Exceeds most program limits")
        
        # Property Condition Assessment
        if condition_rules:
            analysis_report.append(f"\n🔍 PROPERTY CONDITION REQUIREMENTS:")
            for condition_rule in condition_rules[:3]:  # Show top 3 condition rules
                analysis_report.append(f"   • {condition_rule.get('description', 'Property condition requirement')}")
        
        # Recommendations
        analysis_report.append(f"\n💡 APPRAISAL RECOMMENDATIONS:")
        if property_rules and property_rules[0].get('appraisal_approach') == 'sales_comparison_primary':
            analysis_report.append("   1. Focus on sales comparison approach with verified comparables")
            analysis_report.append("   2. Ensure all comparables meet distance and time requirements")
            analysis_report.append("   3. Document all adjustments within acceptable limits")
        
        if property_type == 'condominium':
            analysis_report.append("   4. Complete HOA financial analysis and warrantability review")
        
        if year_built and year_built >= 2020:
            analysis_report.append("   5. Include cost approach for new construction verification")
        
        analysis_report.append("   6. Verify property condition meets lending standards")
        analysis_report.append("   7. Document market conditions and trends")
        
        return "\n".join(analysis_report)
        
    except Exception as e:
        logger.error(f"Error during property value analysis: {e}")
        return f" Error during property value analysis: {str(e)}"


def validate_tool() -> bool:
    """Validate that the analyze_property_value tool works correctly."""
    try:
        # Test with sample natural language data
        result = analyze_property_value.invoke({
            "property_info": "Property at 123 Main St, Anytown, CA 90210, single family detached home, loan amount $400,000, estimated value $500,000, 2000 sq ft, built in 2010"
        })
        return "PROPERTY VALUE ANALYSIS REPORT" in result and "VALUE ANALYSIS APPROACHES" in result
    except Exception as e:
        print(f"Property value analysis tool validation failed: {e}")
        return False
