"""
Market Conditions Evaluation Tool

This tool evaluates market conditions affecting property value
based on Neo4j property appraisal rules.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from datetime import datetime, timedelta

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection

logger = logging.getLogger(__name__)


class MarketConditionsRequest(BaseModel):
    """Market conditions evaluation request parameters."""
    property_address: str = Field(..., description="Property address")
    property_type: str = Field(..., description="Property type")
    market_area: str = Field(..., description="Market area or neighborhood")
    price_range: str = Field(..., description="Price range (e.g., 400000-600000)")
    days_on_market: Optional[int] = Field(None, description="Average days on market")
    inventory_levels: Optional[str] = Field("normal", description="Inventory levels (low, normal, high)")
    price_trend: Optional[str] = Field("stable", description="Recent price trend (declining, stable, increasing)")
    absorption_rate: Optional[float] = Field(None, description="Absorption rate (months of inventory)")
    median_sale_price: Optional[float] = Field(None, description="Current median sale price")
    prior_year_median: Optional[float] = Field(None, description="Prior year median sale price")


@tool(args_schema=MarketConditionsRequest)
def evaluate_market_conditions(
    property_address: str,
    property_type: str,
    market_area: str,
    price_range: str,
    days_on_market: Optional[int] = None,
    inventory_levels: Optional[str] = "normal",
    price_trend: Optional[str] = "stable",
    absorption_rate: Optional[float] = None,
    median_sale_price: Optional[float] = None,
    prior_year_median: Optional[float] = None
) -> str:
    """
    Evaluate market conditions affecting property value using Neo4j appraisal rules.
    
    This tool analyzes current market conditions and their impact on property
    valuation and lending decisions.
    """
    
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
            market_rules = [dict(record['rule']) for record in result]
            
            # Get appraisal standards for market analysis
            standards_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'AppraisalStandards'
            RETURN rule
            """
            result = session.run(standards_rules_query)
            standards_rules = [dict(record['rule']) for record in result]
        
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
        # Test with sample data
        result = evaluate_market_conditions.invoke({
            "property_address": "123 Main St, Anytown, CA 90210",
            "property_type": "single_family_detached",
            "market_area": "Anytown Suburbs",
            "price_range": "400000-600000",
            "days_on_market": 45,
            "inventory_levels": "normal",
            "price_trend": "stable",
            "absorption_rate": 4.2,
            "median_sale_price": 525000.0,
            "prior_year_median": 510000.0
        })
        return "MARKET CONDITIONS EVALUATION REPORT" in result and "MARKET OUTLOOK" in result
    except Exception as e:
        print(f"Market conditions evaluation tool validation failed: {e}")
        return False
