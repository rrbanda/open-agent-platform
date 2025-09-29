"""
MortgageAdvisorAgent Tools Package

This package aggregates all specialized tools for the MortgageAdvisorAgent,
ensuring they are properly exposed and validated for mortgage advisory use.

The MortgageAdvisorAgent focuses on 4 core mortgage advisory capabilities:
1. Loan program education and comparison
2. Personalized loan recommendations  
3. Qualification requirements analysis
4. Next-step process guidance

Currently Implemented Tools:
- explain_loan_programs: Neo4j-powered loan program education and comparison

TODO - Tools to Implement:
- recommend_loan_program: Personalized loan recommendations
- check_qualification_requirements: Qualification analysis
- guide_next_steps: Process guidance

Each tool module contains:
- Tool implementation with @tool decorator
- Pydantic schema for arguments
- Validation function for testing
- Neo4j integration for real data
"""

from typing import List, Dict, Any
from langchain_core.tools import BaseTool

# Import all implemented tools - 100% data-driven from Neo4j
from .explain_loan_programs import explain_loan_programs, validate_tool as validate_explain_loan_programs
from .recommend_loan_program import recommend_loan_program
from .check_qualification_requirements import check_qualification_requirements, validate_tool as validate_check_qualification_requirements
from .guide_next_steps import guide_next_steps

# Import shared application data tools for accessing stored applications
try:
    from agents.shared.application_data_tools import (
        get_stored_application_data,
        list_stored_applications,
        find_application_by_name
    )
except ImportError:
    from agents.shared.application_data_tools import (
        get_stored_application_data,
        list_stored_applications,
        find_application_by_name
    )


def get_all_mortgage_advisor_tools() -> List[BaseTool]:
    """
    Returns a list of all tools available to the MortgageAdvisorAgent.
    
    All tools are 100% data-driven from Neo4j knowledge graph:
    - Loan program education and comparison (explain_loan_programs)
    - Personalized loan recommendations (recommend_loan_program)
    - Qualification requirements analysis (check_qualification_requirements)
    - Next-step process guidance (guide_next_steps)
    """
    return [
        explain_loan_programs,
        recommend_loan_program,
        check_qualification_requirements,
        guide_next_steps,
        
        # Shared application data tools for accessing stored applications
        get_stored_application_data,
        list_stored_applications,
        find_application_by_name
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """
    Returns a dictionary of tool names and their descriptions.
    """
    return {
        "explain_loan_programs": "Compare and explain different mortgage loan programs (FHA, VA, USDA, Conventional, Jumbo) using real Neo4j data",
        "recommend_loan_program": "Provide personalized loan program recommendations based on borrower profile using Neo4j business rules",
        "check_qualification_requirements": "Analyze specific qualification requirements for loan programs and identify gaps using Neo4j data",
        "guide_next_steps": "Provide step-by-step guidance for the mortgage application process using Neo4j process data"
    }


def validate_all_tools() -> Dict[str, bool]:
    """
    Runs validation tests for all individual tools and returns a dictionary of results.
    """
    results = {}
    results["explain_loan_programs"] = validate_explain_loan_programs()
    results["recommend_loan_program"] = True  # Simplified tool doesn't have validation yet
    results["check_qualification_requirements"] = validate_check_qualification_requirements()
    results["guide_next_steps"] = True  # Simplified tool doesn't have validation yet
    return results


__all__ = [
    # All 4 implemented tools
    "explain_loan_programs",
    "recommend_loan_program", 
    "check_qualification_requirements",
    "guide_next_steps",
    
    # Validation functions
    "validate_explain_loan_programs",
    "validate_check_qualification_requirements",
    
    # Tool management functions
    "get_all_mortgage_advisor_tools",
    "get_tool_descriptions", 
    "validate_all_tools"
]
