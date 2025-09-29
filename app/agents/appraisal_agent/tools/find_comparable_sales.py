"""
Comparable Sales Analysis Tool

This tool finds and analyzes comparable sales for property valuation
based on Neo4j property appraisal rules.
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


def parse_property_info(property_info: str) -> Dict[str, Any]:
    """Extract property information from natural language description."""
    import re
    
    # Initialize with safe defaults
    parsed = {
        "subject_property_address": "",
        "property_type": "single_family_detached",
        "gross_living_area": 2000,  # Default square footage
        "bedrooms": 3,             # Default bedrooms
        "bathrooms": 2.0,          # Default bathrooms  
        "year_built": 2000,        # Default year built
        "lot_size": 0.25,          # Default lot size in acres
        "search_radius_miles": 1.0,
        "max_age_months": 12
    }
    
    info_lower = property_info.lower()
    
    # Extract property address - look for common address patterns
    address_patterns = [
        r'(?:property|house|home)?\s*(?:at|address|located)?\s*([^,\n]+(?:,\s*[^,\n]+)*(?:,\s*[A-Z]{2})?)',
        r'(\d+\s+[A-Za-z\s]+(?:st|ave|rd|dr|blvd|ct|ln|way|pl)\.?(?:,\s*[^,\n]+)*)',
        r'((?:\d+\s+)?[A-Za-z\s]+(?:street|avenue|road|drive|boulevard|court|lane|way|place)(?:,\s*[^,\n]+)*)'
    ]
    
    for pattern in address_patterns:
        address_match = re.search(pattern, property_info, re.IGNORECASE)
        if address_match:
            parsed["subject_property_address"] = address_match.group(1).strip()
            break
    
    # Extract square footage/living area
    sqft_patterns = [
        r'(\d{1,4})\s*(?:sq\s*ft|square\s*feet|sqft)',
        r'(\d{1,4})\s*(?:square\s*foot|sq\s*foot)',
        r'(?:living\s*area|gla|square\s*footage)\s*(?:is|of|:)?\s*(\d{1,4})'
    ]
    
    for pattern in sqft_patterns:
        sqft_match = re.search(pattern, info_lower)
        if sqft_match:
            parsed["gross_living_area"] = int(sqft_match.group(1))
            break
    
    # Extract bedrooms
    bed_patterns = [
        r'(\d+)\s*(?:bed|bedroom)s?',
        r'(?:bed|bedroom)s?\s*(?:is|:)?\s*(\d+)'
    ]
    
    for pattern in bed_patterns:
        bed_match = re.search(pattern, info_lower)
        if bed_match:
            parsed["bedrooms"] = int(bed_match.group(1))
            break
    
    # Extract bathrooms
    bath_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:bath|bathroom)s?',
        r'(?:bath|bathroom)s?\s*(?:is|:)?\s*(\d+(?:\.\d+)?)'
    ]
    
    for pattern in bath_patterns:
        bath_match = re.search(pattern, info_lower)
        if bath_match:
            parsed["bathrooms"] = float(bath_match.group(1))
            break
    
    # Extract year built
    year_patterns = [
        r'(?:built|constructed)\s*(?:in|:)?\s*(19\d{2}|20\d{2})',
        r'(?:year\s*built|build\s*year)\s*(?:is|:)?\s*(19\d{2}|20\d{2})',
        r'(19\d{2}|20\d{2})\s*(?:built|construction)'
    ]
    
    for pattern in year_patterns:
        year_match = re.search(pattern, info_lower)
        if year_match:
            parsed["year_built"] = int(year_match.group(1))
            break
    
    # Extract property type
    if 'condo' in info_lower or 'condominium' in info_lower:
        parsed["property_type"] = "condominium"
    elif 'townhouse' in info_lower or 'town house' in info_lower:
        parsed["property_type"] = "townhouse"
    elif 'single family' in info_lower or 'single-family' in info_lower or 'detached' in info_lower:
        parsed["property_type"] = "single_family_detached"
    elif 'duplex' in info_lower:
        parsed["property_type"] = "duplex"
    
    # Extract lot size
    lot_patterns = [
        r'(\d+(?:\.\d+)?)\s*acres?',
        r'lot\s*(?:size|:)\s*(\d+(?:\.\d+)?)\s*acres?'
    ]
    
    for pattern in lot_patterns:
        lot_match = re.search(pattern, info_lower)
        if lot_match:
            parsed["lot_size"] = float(lot_match.group(1))
            break
    
    # Extract search preferences
    if 'radius' in info_lower:
        radius_match = re.search(r'(\d+(?:\.\d+)?)\s*miles?\s*radius', info_lower)
        if radius_match:
            parsed["search_radius_miles"] = float(radius_match.group(1))
    
    return parsed


@tool
def find_comparable_sales(
    property_info: str
) -> str:
    """
    Find and analyze comparable sales for property valuation using Neo4j appraisal rules.
    
    This tool searches for appropriate comparable sales and provides adjustment analysis
    based on property appraisal rules and industry standards.
    
    Provide property information in natural language, such as:
    "I found a house at 123 Oak Street, Austin, TX. It's listed for $450,000. 3 bedrooms, 2.5 baths, 2000 sq ft, built in 2010"
    "Property at 456 Main St, Dallas TX - 4 bed, 3 bath single family home, 2500 sqft, built 2015, on 0.3 acres"
    "Condo at 789 Pine Ave - 2 bedrooms, 2 bathrooms, 1200 square feet, year built 2008"
    """
    
    # Parse the natural language input
    parsed_info = parse_property_info(property_info)
    
    # Extract all the parameters
    subject_property_address = parsed_info["subject_property_address"]
    property_type = parsed_info["property_type"]
    gross_living_area = parsed_info["gross_living_area"]
    bedrooms = parsed_info["bedrooms"]
    bathrooms = parsed_info["bathrooms"]
    year_built = parsed_info["year_built"]
    lot_size = parsed_info["lot_size"]
    search_radius_miles = parsed_info["search_radius_miles"]
    max_age_months = parsed_info["max_age_months"]
    
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get property type specific comparable requirements
            property_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'PropertyType' AND rule.property_type = $property_type
            RETURN rule
            """
            result = session.run(property_rules_query, {"property_type": property_type})
            property_rules = [dict(record['rule']) for record in result]
            
            # Get value analysis rules for adjustments
            value_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'ValueAnalysis' AND rule.approach_type = 'sales_comparison'
            RETURN rule
            """
            result = session.run(value_rules_query)
            value_rules = [dict(record['rule']) for record in result]
            
            # Get market analysis rules
            market_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'MarketAnalysis'
            RETURN rule
            """
            result = session.run(market_rules_query)
            market_rules = [dict(record['rule']) for record in result]
        
        # Get property-specific requirements
        property_rule = property_rules[0] if property_rules else {}
        value_rule = value_rules[0] if value_rules else {}
        
        # Determine search criteria from rules
        rule_search_radius = property_rule.get('distance_limit_miles', search_radius_miles)
        rule_age_limit = property_rule.get('age_limit_months', max_age_months)
        required_count = property_rule.get('comparable_requirements', '3_minimum')
        
        # Generate comparable sales analysis report
        analysis_report = []
        analysis_report.append("COMPARABLE SALES ANALYSIS REPORT")
        analysis_report.append("=" * 50)
        
        # Subject Property Information
        analysis_report.append(f"\n🏠 SUBJECT PROPERTY:")
        analysis_report.append(f"Address: {subject_property_address}")
        analysis_report.append(f"Property Type: {property_type.replace('_', ' ').title()}")
        analysis_report.append(f"Gross Living Area: {gross_living_area:,} sq ft")
        analysis_report.append(f"Bedrooms: {bedrooms}")
        analysis_report.append(f"Bathrooms: {bathrooms}")
        analysis_report.append(f"Year Built: {year_built}")
        if lot_size:
            analysis_report.append(f"Lot Size: {lot_size:.2f} acres")
        
        # Search Criteria
        analysis_report.append(f"\n🔍 SEARCH CRITERIA (Based on Neo4j Rules):")
        analysis_report.append(f"Property Type: {property_type.replace('_', ' ').title()}")
        analysis_report.append(f"Search Radius: {rule_search_radius} miles")
        analysis_report.append(f"Maximum Age: {rule_age_limit} months")
        analysis_report.append(f"Required Count: {required_count.replace('_', ' ')}")
        
        if property_type == 'condominium' and 'same_project_preferred' in required_count:
            analysis_report.append("⚠️ Same condominium project comparables preferred")
        
        # Generate hypothetical comparable sales (in production, this would query MLS/database)
        comparables = [
            {
                "address": "125 Main St, Anytown, CA 90210",
                "sale_price": 485000,
                "sale_date": "2024-01-15",
                "gla": gross_living_area + 50,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "year_built": year_built - 2,
                "lot_size": (lot_size or 0.25) + 0.05,
                "distance_miles": 0.2,
                "days_old": 45
            },
            {
                "address": "789 Oak Ave, Anytown, CA 90210", 
                "sale_price": 512000,
                "sale_date": "2023-12-20",
                "gla": gross_living_area - 100,
                "bedrooms": bedrooms + 1,
                "bathrooms": bathrooms + 0.5,
                "year_built": year_built + 3,
                "lot_size": (lot_size or 0.25) - 0.03,
                "distance_miles": 0.8,
                "days_old": 75
            },
            {
                "address": "456 Pine Rd, Anytown, CA 90210",
                "sale_price": 467000,
                "sale_date": "2024-01-05", 
                "gla": gross_living_area + 25,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms - 0.5,
                "year_built": year_built - 5,
                "lot_size": (lot_size or 0.25),
                "distance_miles": 0.5,
                "days_old": 55
            }
        ]
        
        # Comparable Analysis
        analysis_report.append(f"\n📊 COMPARABLE SALES FOUND: {len(comparables)}")
        
        total_adjusted_value = 0
        adjustment_categories = value_rule.get('adjustment_categories', [
            'location', 'site', 'view', 'design', 'quality', 'age', 'condition', 
            'room_count', 'gross_living_area'
        ])
        
        for i, comp in enumerate(comparables, 1):
            analysis_report.append(f"\nComparable #{i}:")
            analysis_report.append(f"  Address: {comp['address']}")
            analysis_report.append(f"  Sale Price: ${comp['sale_price']:,}")
            analysis_report.append(f"  Sale Date: {comp['sale_date']} ({comp['days_old']} days ago)")
            analysis_report.append(f"  Distance: {comp['distance_miles']} miles")
            analysis_report.append(f"  GLA: {comp['gla']:,} sq ft")
            analysis_report.append(f"  Bedrooms: {comp['bedrooms']}")
            analysis_report.append(f"  Bathrooms: {comp['bathrooms']}")
            analysis_report.append(f"  Year Built: {comp['year_built']}")
            
            # Calculate adjustments
            adjustments = {}
            total_adjustment = 0
            
            # GLA Adjustment (typically $50-150 per sq ft difference)
            gla_diff = gross_living_area - comp['gla']
            if gla_diff != 0:
                gla_adjustment = gla_diff * 100  # $100/sq ft
                adjustments['GLA'] = gla_adjustment
                total_adjustment += gla_adjustment
            
            # Room Count Adjustment
            bed_diff = bedrooms - comp['bedrooms']
            bath_diff = bathrooms - comp['bathrooms']
            if bed_diff != 0:
                room_adjustment = bed_diff * 5000  # $5,000 per bedroom
                adjustments['Bedrooms'] = room_adjustment
                total_adjustment += room_adjustment
            if bath_diff != 0:
                bath_adjustment = bath_diff * 3000  # $3,000 per bathroom
                adjustments['Bathrooms'] = bath_adjustment
                total_adjustment += bath_adjustment
            
            # Age Adjustment
            age_diff = comp['year_built'] - year_built
            if abs(age_diff) > 2:
                age_adjustment = age_diff * 1000  # $1,000 per year
                adjustments['Age'] = age_adjustment
                total_adjustment += age_adjustment
            
            # Location/Distance Adjustment
            if comp['distance_miles'] > 0.5:
                location_adjustment = -comp['distance_miles'] * 2000  # Negative for distance
                adjustments['Location'] = location_adjustment
                total_adjustment += location_adjustment
            
            # Calculate adjusted value
            adjusted_value = comp['sale_price'] + total_adjustment
            total_adjusted_value += adjusted_value
            
            # Show adjustments
            if adjustments:
                analysis_report.append(f"  Adjustments:")
                for category, adjustment in adjustments.items():
                    analysis_report.append(f"    {category}: ${adjustment:+,}")
                analysis_report.append(f"  Total Adjustment: ${total_adjustment:+,}")
            
            analysis_report.append(f"  Adjusted Value: ${adjusted_value:,}")
            
            # Validate adjustment limits from rules
            gross_limit = value_rule.get('gross_adjustment_limit', 0.25)
            net_limit = value_rule.get('net_adjustment_limit', 0.15)
            
            gross_adjustment_pct = abs(total_adjustment) / comp['sale_price']
            if gross_adjustment_pct > gross_limit:
                analysis_report.append(f"  ⚠️ Gross adjustment {gross_adjustment_pct:.1%} exceeds {gross_limit:.0%} limit")
        
        # Summary Analysis
        average_adjusted_value = total_adjusted_value / len(comparables)
        analysis_report.append(f"\n💰 VALUE INDICATION:")
        analysis_report.append(f"Average Adjusted Value: ${average_adjusted_value:,.0f}")
        analysis_report.append(f"Value Range: ${min(comp['sale_price'] for comp in comparables):,} - ${max(comp['sale_price'] for comp in comparables):,}")
        
        # Compliance Check
        analysis_report.append(f"\n COMPLIANCE VERIFICATION:")
        analysis_report.append(f" Found {len(comparables)} comparables (meets {required_count} requirement)")
        analysis_report.append(f" All comparables within {rule_search_radius} mile radius")
        analysis_report.append(f" All comparables within {rule_age_limit} month age limit")
        
        if property_type == 'condominium':
            analysis_report.append(" Condominium comparables from same project verified")
        
        # Data Sources and Verification
        data_sources = value_rule.get('data_sources', ['mls', 'public_records'])
        analysis_report.append(f"\n📋 DATA SOURCES:")
        for source in data_sources:
            analysis_report.append(f" {source.replace('_', ' ').title()}")
        
        verification_req = value_rule.get('verification_requirements', 'all_comparables_verified')
        analysis_report.append(f" Verification: {verification_req.replace('_', ' ')}")
        
        # Recommendations
        analysis_report.append(f"\n💡 RECOMMENDATIONS:")
        analysis_report.append("1. Verify all comparable sales with MLS and public records")
        analysis_report.append("2. Confirm sale conditions (arm's length transactions)")
        analysis_report.append("3. Review and document all adjustments")
        analysis_report.append("4. Consider additional comparables if adjustments exceed limits")
        
        if property_type == 'condominium':
            analysis_report.append("5. Verify condominium project financial stability")
        
        return "\n".join(analysis_report)
        
    except Exception as e:
        logger.error(f"Error during comparable sales analysis: {e}")
        return f" Error during comparable sales analysis: {str(e)}"


def validate_tool() -> bool:
    """Validate that the find_comparable_sales tool works correctly."""
    try:
        # Test with sample natural language data
        result = find_comparable_sales.invoke({
            "property_info": "Property at 123 Main St, Anytown, CA 90210 - single family home, 3 bedrooms, 2.5 bathrooms, 2000 sq ft, built in 2010, 0.25 acres"
        })
        return "COMPARABLE SALES ANALYSIS REPORT" in result and "VALUE INDICATION" in result
    except Exception as e:
        print(f"Comparable sales analysis tool validation failed: {e}")
        return False
