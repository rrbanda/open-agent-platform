"""
ApplicationAgent - Intelligent Mortgage Application Intake and Workflow Coordination

This agent provides comprehensive mortgage application management and workflow coordination
using specialized tools and Neo4j knowledge graph integration for rule-based processing.

The ApplicationAgent specializes in:
- Mortgage application intake and validation with comprehensive data verification
- Application completeness verification against loan type and employment requirements
- Initial qualification assessment and pre-screening across multiple loan programs
- Workflow routing coordination and intelligent agent handoffs
- Application status tracking, milestone management, and progress reporting
- Neo4j knowledge graph integration for rule-driven application decisions

Structure:
- agent.py: Main agent creation and configuration
- prompts.yaml: Co-located prompt definitions specific to application intake
- tools/: Individual tool modules for focused application management capabilities
- tests/: Comprehensive test suite for application functionality
- ../shared/: Reusable utilities shared across all agents (prompt loader, etc.)

Tools (All 5 implemented - 100% data-driven from Neo4j):
- receive_mortgage_application: Complete application intake with validation and initial processing
- check_application_completeness: Verify all required documentation and data completeness
- perform_initial_qualification: Initial qualification assessment and loan program recommendations
- track_application_status: Comprehensive status tracking and milestone management

Benefits:
- Focused application intake expertise with deep workflow knowledge
- Intelligent, rule-based application processing using Neo4j knowledge graph
- Clear separation from specialized processing concerns (documents, appraisal, underwriting)
- Professional and consistent application management
- Seamless coordination across all specialized agents
"""

from .agent import create_application_agent
from .tools import (
    receive_mortgage_application,
    check_application_completeness,
    perform_initial_qualification,
    track_application_status,
    get_all_application_agent_tools,
    validate_all_tools
)
from agents.shared.prompt_loader import (
    load_agent_prompt as load_application_prompt,
    get_agent_prompt_loader,
    validate_agent_prompts
)

__all__ = [
    # Main agent
    "create_application_agent",
    
    # All 5 implemented tools - 100% data-driven from Neo4j
    "receive_mortgage_application",
    "check_application_completeness",
    "perform_initial_qualification",
    "track_application_status",
    
    # Tool management
    "get_all_application_agent_tools",
    "validate_all_tools",
    
    # Prompt management (shared utilities)
    "load_application_prompt",
    "get_agent_prompt_loader",
    "validate_agent_prompts"
]
