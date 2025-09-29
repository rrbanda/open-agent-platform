"""
AppraisalAgent Tools Package

This package aggregates all specialized tools for the AppraisalAgent,
ensuring they are properly exposed and validated for property appraisal use.

The AppraisalAgent focuses on 5 core property appraisal capabilities:
1. Property value analysis using multiple appraisal approaches
2. Comparable sales research and analysis
3. Property condition assessment for lending
4. Appraisal report review and compliance validation
5. Market conditions evaluation and impact analysis

Currently Implemented Tools (All 5 - 100% data-driven from Neo4j):
- analyze_property_value: Comprehensive property valuation analysis
- find_comparable_sales: Comparable sales research and adjustment analysis
- assess_property_condition: Property condition evaluation for lending standards
- review_appraisal_report: Appraisal report compliance and quality review
- evaluate_market_conditions: Market analysis and valuation impact assessment

Each tool module contains:
- Tool implementation with @tool decorator
- Pydantic schema for arguments
- Validation function for testing
- Neo4j integration for real appraisal rules
"""

from typing import List, Dict, Any
from langchain_core.tools import BaseTool

# Import all implemented tools - 100% data-driven from Neo4j
from .analyze_property_value import analyze_property_value, validate_tool as validate_analyze_property_value
from .find_comparable_sales import find_comparable_sales, validate_tool as validate_find_comparable_sales
from .assess_property_condition import assess_property_condition, validate_tool as validate_assess_property_condition
from .review_appraisal_report import review_appraisal_report, validate_tool as validate_review_appraisal_report
from .evaluate_market_conditions import evaluate_market_conditions, validate_tool as validate_evaluate_market_conditions


def get_all_appraisal_agent_tools() -> List[BaseTool]:
    """
    Returns a list of all tools available to the AppraisalAgent.
    
    All tools are 100% data-driven from Neo4j knowledge graph:
    - Property value analysis using multiple approaches (analyze_property_value)
    - Comparable sales research and analysis (find_comparable_sales)
    - Property condition assessment for lending (assess_property_condition)
    - Appraisal report review and compliance (review_appraisal_report)
    - Market conditions evaluation and impact (evaluate_market_conditions)
    """
    return [
        analyze_property_value,
        find_comparable_sales,
        assess_property_condition,
        review_appraisal_report,
        evaluate_market_conditions
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """
    Returns a dictionary of tool names and their descriptions.
    """
    return {
        "analyze_property_value": "Comprehensive property valuation analysis using sales comparison, cost, and income approaches based on Neo4j appraisal rules",
        "find_comparable_sales": "Find and analyze comparable sales with adjustment analysis based on property type and market requirements from Neo4j",
        "assess_property_condition": "Evaluate property condition for lending standards and loan program requirements using Neo4j condition rules",
        "review_appraisal_report": "Review and validate appraisal reports for compliance with industry standards and loan program requirements from Neo4j",
        "evaluate_market_conditions": "Analyze market conditions and their impact on property valuation and lending decisions using Neo4j market rules"
    }


def validate_all_tools() -> Dict[str, bool]:
    """
    Runs validation tests for all individual tools and returns a dictionary of results.
    """
    results = {}
    results["analyze_property_value"] = validate_analyze_property_value()
    results["find_comparable_sales"] = validate_find_comparable_sales()
    results["assess_property_condition"] = validate_assess_property_condition()
    results["review_appraisal_report"] = validate_review_appraisal_report()
    results["evaluate_market_conditions"] = validate_evaluate_market_conditions()
    return results


__all__ = [
    # All 5 implemented tools
    "analyze_property_value",
    "find_comparable_sales",
    "assess_property_condition",
    "review_appraisal_report",
    "evaluate_market_conditions",
    
    # Validation functions
    "validate_analyze_property_value",
    "validate_find_comparable_sales",
    "validate_assess_property_condition", 
    "validate_review_appraisal_report",
    "validate_evaluate_market_conditions",
    
    # Tool management functions
    "get_all_appraisal_agent_tools",
    "get_tool_descriptions", 
    "validate_all_tools"
]
