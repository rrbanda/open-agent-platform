"""
ApplicationAgent Tools Package

This package aggregates all specialized tools for the ApplicationAgent,
ensuring they are properly exposed and validated for mortgage application intake use.

The ApplicationAgent focuses on 6 core application management capabilities:
1. Mortgage application intake and validation
2. Application completeness verification
3. Initial qualification assessment and pre-screening
4. Workflow routing coordination across agents
5. Application status tracking and management
6. URLA Form 1003 generation and compliance

Currently Implemented Tools (All 6 - 100% data-driven from Neo4j):
- receive_mortgage_application: Complete application intake and validation
- check_application_completeness: Verify all required documentation and data
- perform_initial_qualification: Pre-screening and qualification assessment
- track_application_status: Comprehensive status tracking and milestone management
- generate_urla_1003_form: Standardized URLA Form 1003 generation with compliance validation

Each tool module contains:
- Tool implementation with @tool decorator
- Pydantic schema for arguments
- Validation function for testing
- Neo4j integration for real application intake rules
"""

from typing import List, Dict, Any
from langchain_core.tools import BaseTool

# Import all implemented tools - 100% data-driven from Neo4j
from .receive_mortgage_application import receive_mortgage_application, validate_tool as validate_receive_mortgage_application
from .check_application_completeness import check_application_completeness, validate_tool as validate_check_application_completeness
from .perform_initial_qualification import perform_initial_qualification, validate_tool as validate_perform_initial_qualification
from .track_application_status import track_application_status, validate_tool as validate_track_application_status
from .generate_urla_1003_form import generate_urla_1003_form, validate_tool as validate_generate_urla_1003_form

# Import shared application data tools for all agents
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


def get_all_application_agent_tools() -> List[BaseTool]:
    """
    Returns a list of all tools available to the ApplicationAgent.
    
    All tools are 100% data-driven from Neo4j knowledge graph:
    - Mortgage application intake and validation (receive_mortgage_application)
    - Application completeness verification (check_application_completeness)
    - Initial qualification assessment (perform_initial_qualification)
    - Application status tracking and management (track_application_status)
    - URLA Form 1003 generation and compliance (generate_urla_1003_form)
    """
    return [
        receive_mortgage_application,  # Now enabled - application storage functionality
        check_application_completeness,
        perform_initial_qualification,
        track_application_status,
        generate_urla_1003_form,
        
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
        "receive_mortgage_application": "Complete mortgage application intake with validation and initial processing using Neo4j application rules",
        "check_application_completeness": "Verify application completeness against loan type and employment requirements using Neo4j validation rules",
        "perform_initial_qualification": "Assess initial qualification across multiple loan programs and provide routing recommendations using Neo4j qualification rules",
        "track_application_status": "Comprehensive application status tracking, milestone management, and progress reporting using Neo4j status rules",
        "generate_urla_1003_form": "Generate standardized URLA Form 1003 from application data with compliance validation using Neo4j URLA rules"
    }


def validate_all_tools() -> Dict[str, bool]:
    """
    Runs validation tests for all individual tools and returns a dictionary of results.
    """
    results = {}
    results["receive_mortgage_application"] = validate_receive_mortgage_application()
    results["check_application_completeness"] = validate_check_application_completeness()
    results["perform_initial_qualification"] = validate_perform_initial_qualification()
    results["track_application_status"] = validate_track_application_status()
    results["generate_urla_1003_form"] = validate_generate_urla_1003_form()
    return results


__all__ = [
    # All 6 implemented tools
    "receive_mortgage_application",
    "check_application_completeness",
    "perform_initial_qualification",
    "track_application_status",
    "generate_urla_1003_form",
    
    # Validation functions
    "validate_receive_mortgage_application",
    "validate_check_application_completeness",
    "validate_perform_initial_qualification",
    "validate_track_application_status",
    "validate_generate_urla_1003_form",
    
    # Tool management functions
    "get_all_application_agent_tools",
    "get_tool_descriptions", 
    "validate_all_tools"
]
