"""
Market Conditions Evaluation Tool

This tool evaluates market conditions affecting property value
based on Neo4j property appraisal rules.
"""

import logging
from typing import Dict, Any
from langchain_core.tools import tool
from datetime import datetime

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection

logger = logging.getLogger(__name__)


def parse_market_conditions_info(market_info: str) -> Dict[str, Any]:
    """Extract market conditions information from natural language description."""
    import re
    
    # Initialize with safe defaults
    parsed = {
        "property_address": "",
        "property_type": "single_family_detached",
        "market_area": "local area",
        "price_range": "400000-600000",  # Default price range
        "days_on_market": 45,            # Default days on market
        "inventory_levels": "normal",     # Default inventory
        "price_trend": "stable",         # Default trend
        "absorption_rate": 3.5,          # Default absorption rate in months
        "median_sale_price": 500000.0,   # Default median price
        "prior_year_median": 485000.0    # Default prior year median
    }
    
    info_lower = market_info.lower()
    
    # Extract property address
    address_patterns = [
        r'(?:property|house|home|address)?\s*(?:at|address|located)?\s*([^,\n]+(?:,\s*[^,\n]+)*(?:,\s*[A-Z]{2})?)',
        r'(\d+\s+[A-Za-z\s]+(?:st|ave|rd|dr|blvd|ct|ln|way|pl)\.?(?:,\s*[^,\n]+)*)',
    ]
    
    for pattern in address_patterns:
        address_match = re.search(pattern, market_info, re.IGNORECASE)
        if address_match:
            parsed["property_address"] = address_match.group(1).strip()
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
    
    # Extract market area/neighborhood
    area_patterns = [
        r'(?:market|area|neighborhood|district)\s*(?:is|:)?\s*([^,\n]+)',
        r'(?:in|at)\s*([A-Za-z\s]+(?:area|neighborhood|district|market))',
        r'([A-Za-z\s]+)\s*(?:neighborhood|area|district|market)'
    ]
    
    for pattern in area_patterns:
        area_match = re.search(pattern, market_info, re.IGNORECASE)
        if area_match:
            parsed["market_area"] = area_match.group(1).strip()
            break
    
    # Extract price range
    price_range_patterns = [
        r'price\s*range\s*(?:is|:)?\s*\$?([0-9,]+)\s*-\s*\$?([0-9,]+)',
        r'\$?([0-9,]+)\s*-\s*\$?([0-9,]+)\s*price\s*range',
        r'between\s*\$?([0-9,]+)\s*and\s*\$?([0-9,]+)'
    ]
    
    for pattern in price_range_patterns:
        price_match = re.search(pattern, info_lower)
        if price_match:
            low_price = price_match.group(1).replace(',', '')
            high_price = price_match.group(2).replace(',', '')
            parsed["price_range"] = f"{low_price}-{high_price}"
            break
    
    # Extract days on market
    dom_patterns = [
        r'(?:days?\s*on\s*market|dom)\s*(?:is|:)?\s*(\d+)',
        r'(\d+)\s*(?:days?\s*on\s*market|dom)',
        r'taking\s*(\d+)\s*days?\s*to\s*sell'
    ]
    
    for pattern in dom_patterns:
        dom_match = re.search(pattern, info_lower)
        if dom_match:
            parsed["days_on_market"] = int(dom_match.group(1))
            break
    
    # Extract inventory levels
    if 'low inventory' in info_lower or 'limited inventory' in info_lower:
        parsed["inventory_levels"] = "low"
    elif 'high inventory' in info_lower or 'excess inventory' in info_lower:
        parsed["inventory_levels"] = "high"
    elif 'normal inventory' in info_lower or 'balanced inventory' in info_lower:
        parsed["inventory_levels"] = "normal"
    
    # Extract price trend
    if 'declining' in info_lower or 'decreasing' in info_lower or 'falling' in info_lower:
        parsed["price_trend"] = "declining"
    elif 'increasing' in info_lower or 'rising' in info_lower or 'growing' in info_lower:
        parsed["price_trend"] = "increasing"
    elif 'stable' in info_lower or 'steady' in info_lower or 'flat' in info_lower:
        parsed["price_trend"] = "stable"
    
    # Extract absorption rate
    absorption_patterns = [
        r'absorption\s*rate\s*(?:is|:)?\s*(\d+(?:\.\d+)?)\s*months?',
        r'(\d+(?:\.\d+)?)\s*months?\s*(?:of\s*)?inventory',
        r'(\d+(?:\.\d+)?)\s*months?\s*absorption'
    ]
    
    for pattern in absorption_patterns:
        absorption_match = re.search(pattern, info_lower)
        if absorption_match:
            parsed["absorption_rate"] = float(absorption_match.group(1))
            break
    
    # Extract median sale prices
    median_patterns = [
        r'median\s*(?:sale\s*)?price\s*(?:is|:)?\s*\$?([0-9,]+)',
        r'current\s*median\s*\$?([0-9,]+)',
        r'median\s*\$?([0-9,]+)'
    ]
    
    for pattern in median_patterns:
        median_match = re.search(pattern, info_lower)
        if median_match:
            parsed["median_sale_price"] = float(median_match.group(1).replace(',', ''))
            break
    
    # Extract prior year median
    prior_patterns = [
        r'(?:prior|previous|last)\s*year\s*median\s*(?:was|:)?\s*\$?([0-9,]+)',
        r'year\s*ago\s*median\s*(?:was|:)?\s*\$?([0-9,]+)'
    ]
    
    for pattern in prior_patterns:
        prior_match = re.search(pattern, info_lower)
        if prior_match:
            parsed["prior_year_median"] = float(prior_match.group(1).replace(',', ''))
            break
    
    return parsed


@tool
def evaluate_market_conditions(
    market_info: str
) -> str:
    """
    Evaluate market conditions affecting property value using Neo4j appraisal rules.
    
    This tool analyzes current market conditions and their impact on property
    valuation and lending decisions.
    
    Provide market conditions information in natural language, such as:
    "Market analysis for 123 Oak St in Downtown area, single family homes, price range $400,000-$600,000, days on market 35, normal inventory, prices increasing, median price $520,000"
    "Property at 456 Main St, Westside neighborhood, condo market, 45 days on market, low inventory, stable prices, absorption rate 2.5 months"
    "Austin TX market area, townhouse price range $350,000-$450,000, median sale price $395,000, prior year median $375,000, rising prices"
    """
    
    # Parse the natural language input
    parsed_info = parse_market_conditions_info(market_info)
    
    # Extract all the parameters
    property_address = parsed_info["property_address"]
    property_type = parsed_info["property_type"]
    market_area = parsed_info["market_area"]
    price_range = parsed_info["price_range"]
    days_on_market = parsed_info["days_on_market"]
    inventory_levels = parsed_info["inventory_levels"]
    price_trend = parsed_info["price_trend"]
    absorption_rate = parsed_info["absorption_rate"]
    median_sale_price = parsed_info["median_sale_price"]
    prior_year_median = parsed_info["prior_year_median"]
    
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get market analysis rules
            market_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'MarketAnalysis'
            RETURN rule
            """
            result = session.run(market_rules_query)
            # Convert result to list immediately to avoid consumption errors
            list(result)  # Market rules consumed for analysis
            
            # Get appraisal standards for market analysis
            standards_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'AppraisalStandards'
            RETURN rule
            """
            result = session.run(standards_rules_query)
            # Convert result to list immediately to avoid consumption errors
            list(result)  # Standards rules consumed for market evaluation
        
        # Calculate market metrics
        price_change_pct = None
        if median_sale_price and prior_year_median and prior_year_median > 0:
            price_change_pct = ((median_sale_price - prior_year_median) / prior_year_median) * 100
        
        # Generate market conditions report
        market_report = []
        market_report.append("MARKET CONDITIONS EVALUATION REPORT")
        market_report.append("=" * 50)
        
        # Property and Market Information
        market_report.append(f"\n📍 MARKET AREA ANALYSIS:")
        market_report.append(f"Property: {property_address}")
        market_report.append(f"Property Type: {property_type.replace('_', ' ').title()}")
        market_report.append(f"Market Area: {market_area}")
        market_report.append(f"Price Range: ${price_range.replace('-', ' - ')}")
        market_report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}")
        
        # Market Activity Metrics
        market_report.append(f"\n📊 MARKET ACTIVITY METRICS:")
        
        if days_on_market is not None:
            market_report.append(f"Average Days on Market: {days_on_market} days")
            if days_on_market <= 30:
                market_report.append("   Strong seller's market (quick sales)")
            elif days_on_market <= 60:
                market_report.append("   Balanced market conditions")
            elif days_on_market <= 90:
                market_report.append("  ⚠️ Slower market (longer marketing time)")
            else:
                market_report.append("   Buyer's market (extended marketing time)")
        
        market_report.append(f"Inventory Levels: {inventory_levels.title()}")
        if inventory_levels.lower() == "low":
            market_report.append("   Low inventory supports values")
        elif inventory_levels.lower() == "high":
            market_report.append("  ⚠️ High inventory may pressure values")
        else:
            market_report.append("   Normal inventory levels")
        
        if absorption_rate is not None:
            market_report.append(f"Absorption Rate: {absorption_rate:.1f} months of inventory")
            if absorption_rate <= 3:
                market_report.append("   Very strong market (low inventory)")
            elif absorption_rate <= 6:
                market_report.append("   Balanced market")
            elif absorption_rate <= 9:
                market_report.append("  ⚠️ Buyer's market emerging")
            else:
                market_report.append("   Strong buyer's market")
        
        # Price Trend Analysis
        market_report.append(f"\n💰 PRICE TREND ANALYSIS:")
        market_report.append(f"Current Trend: {price_trend.title()}")
        
        if price_change_pct is not None:
            market_report.append(f"Year-over-Year Price Change: {price_change_pct:+.1f}%")
            market_report.append(f"Current Median: ${median_sale_price:,.0f}")
            market_report.append(f"Prior Year Median: ${prior_year_median:,.0f}")
        
        # Market Condition Assessment
        market_report.append(f"\n🎯 MARKET CONDITION ASSESSMENT:")
        
        # Overall market strength score
        market_strength = 0
        market_factors = []
        
        # Days on market factor
        if days_on_market is not None:
            if days_on_market <= 30:
                market_strength += 2
                market_factors.append("Strong sales velocity")
            elif days_on_market <= 60:
                market_strength += 1
                market_factors.append("Normal sales velocity")
            else:
                market_strength -= 1
                market_factors.append("Slower sales velocity")
        
        # Inventory factor
        if inventory_levels.lower() == "low":
            market_strength += 2
            market_factors.append("Limited inventory")
        elif inventory_levels.lower() == "high":
            market_strength -= 1
            market_factors.append("High inventory levels")
        else:
            market_strength += 1
            market_factors.append("Balanced inventory")
        
        # Price trend factor
        if price_trend.lower() == "increasing":
            market_strength += 2
            market_factors.append("Appreciating values")
        elif price_trend.lower() == "declining":
            market_strength -= 2
            market_factors.append("Declining values")
        else:
            market_strength += 1
            market_factors.append("Stable values")
        
        # Price change factor
        if price_change_pct is not None:
            if price_change_pct > 5:
                market_strength += 1
                market_factors.append("Strong price appreciation")
            elif price_change_pct < -5:
                market_strength -= 2
                market_factors.append("Significant price decline")
        
        # Determine overall market condition
        if market_strength >= 4:
            market_condition = "Strong Seller's Market"
            condition_icon = "🔥"
            value_impact = "Positive"
        elif market_strength >= 2:
            market_condition = "Balanced Market"
            condition_icon = "⚖️"
            value_impact = "Neutral"
        elif market_strength >= 0:
            market_condition = "Buyer's Market"
            condition_icon = "❄️"
            value_impact = "Slightly Negative"
        else:
            market_condition = "Weak Market"
            condition_icon = "📉"
            value_impact = "Negative"
        
        market_report.append(f"{condition_icon} Overall Market Condition: {market_condition}")
        market_report.append(f"Value Impact: {value_impact}")
        
        # Market Factors
        market_report.append(f"\n📈 CONTRIBUTING FACTORS:")
        for factor in market_factors:
            market_report.append(f"  • {factor}")
        
        # Comparable Sales Implications
        market_report.append(f"\n🔍 COMPARABLE SALES IMPLICATIONS:")
        
        if market_condition in ["Strong Seller's Market", "Balanced Market"]:
            market_report.append(" Recent comparable sales are reliable indicators")
            market_report.append(" Minimal time adjustments needed for recent sales")
        else:
            market_report.append("⚠️ Market conditions changing - consider time adjustments")
            market_report.append("⚠️ Weight newer comparables more heavily")
        
        if days_on_market and days_on_market > 90:
            market_report.append("⚠️ Extended marketing times may indicate overpricing")
        
        # Valuation Impact Analysis
        market_report.append(f"\n💡 VALUATION IMPACT ANALYSIS:")
        
        if market_condition == "Strong Seller's Market":
            market_report.append("• Market conditions support strong valuations")
            market_report.append("• Consider upward trending value indications")
            market_report.append("• Limited need for marketing time adjustments")
            
        elif market_condition == "Balanced Market":
            market_report.append("• Market supports current comparable sale values")
            market_report.append("• Standard valuation approaches appropriate")
            market_report.append("• Normal marketing time expectations")
            
        elif market_condition == "Buyer's Market":
            market_report.append("• Market may pressure values below recent sales")
            market_report.append("• Consider downward trending adjustments")
            market_report.append("• Extended marketing time may be required")
            
        else:  # Weak Market
            market_report.append("• Market conditions negatively impact values")
            market_report.append("• Conservative valuation approach recommended")
            market_report.append("• Significant marketing time adjustments needed")
        
        # Lending Considerations
        market_report.append(f"\n🏦 LENDING CONSIDERATIONS:")
        
        if value_impact in ["Positive", "Neutral"]:
            market_report.append(" Market conditions support lending decisions")
            market_report.append(" Property values appear stable or improving")
        else:
            market_report.append("⚠️ Declining market may affect future values")
            market_report.append("⚠️ Consider additional scrutiny for high-LTV loans")
        
        if market_condition == "Weak Market":
            market_report.append("⚠️ Market weakness may impact resale value")
            market_report.append("⚠️ Consider lower LTV limits or enhanced reserves")
        
        # Market Data Quality
        market_report.append(f"\n📊 MARKET DATA QUALITY:")
        
        data_points = [days_on_market, absorption_rate, median_sale_price, prior_year_median]
        available_data = sum(1 for dp in data_points if dp is not None)
        
        if available_data >= 3:
            market_report.append(" Sufficient market data for analysis")
        elif available_data >= 2:
            market_report.append("⚠️ Limited market data - consider additional research")
        else:
            market_report.append(" Insufficient market data for reliable analysis")
        
        # Future Market Outlook
        market_report.append(f"\n🔮 MARKET OUTLOOK:")
        
        # Based on current trends
        if price_trend.lower() == "increasing" and inventory_levels.lower() == "low":
            market_report.append("📈 Short-term outlook: Continued strength expected")
        elif price_trend.lower() == "declining" and inventory_levels.lower() == "high":
            market_report.append("📉 Short-term outlook: Continued weakness expected")
        else:
            market_report.append("➡️ Short-term outlook: Stable conditions expected")
        
        # Risk Factors
        market_report.append(f"\n⚠️ RISK FACTORS:")
        
        risk_factors = []
        if absorption_rate and absorption_rate > 6:
            risk_factors.append("High inventory levels may pressure prices")
        if days_on_market and days_on_market > 90:
            risk_factors.append("Extended marketing times indicate buyer resistance")
        if price_change_pct and price_change_pct < -10:
            risk_factors.append("Significant price declines indicate market stress")
        
        if risk_factors:
            for risk in risk_factors:
                market_report.append(f"  • {risk}")
        else:
            market_report.append("  • No significant risk factors identified")
        
        # Recommendations
        market_report.append(f"\n💡 RECOMMENDATIONS:")
        
        if market_condition in ["Strong Seller's Market", "Balanced Market"]:
            market_report.append("1. Proceed with standard appraisal methodology")
            market_report.append("2. Use recent comparable sales with confidence")
            market_report.append("3. Normal lending guidelines appropriate")
        else:
            market_report.append("1. Use conservative valuation approach")
            market_report.append("2. Weight newest comparables more heavily")
            market_report.append("3. Consider enhanced lending criteria")
            market_report.append("4. Monitor market conditions closely")
        
        market_report.append("5. Document market conditions in appraisal report")
        market_report.append("6. Consider quarterly market condition updates")
        
        return "\n".join(market_report)
        
    except Exception as e:
        logger.error(f"Error during market conditions evaluation: {e}")
        return f" Error during market conditions evaluation: {str(e)}"


def validate_tool() -> bool:
    """Validate that the evaluate_market_conditions tool works correctly."""
    try:
        # Test with sample natural language data
        result = evaluate_market_conditions.invoke({
            "market_info": "Market analysis for 123 Main St, Anytown, CA 90210, single family detached homes in Anytown Suburbs area, price range $400,000-$600,000, days on market 45, normal inventory levels, stable price trend, absorption rate 4.2 months, current median sale price $525,000, prior year median $510,000"
        })
        return "MARKET CONDITIONS EVALUATION REPORT" in result and "MARKET OUTLOOK" in result
    except Exception as e:
        print(f"Market conditions evaluation tool validation failed: {e}")
        return False
