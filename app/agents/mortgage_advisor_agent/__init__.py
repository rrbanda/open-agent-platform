"""
MortgageAdvisorAgent - Intelligent Mortgage Guidance and Education

This agent provides comprehensive mortgage guidance, loan program education,
and personalized recommendations to help users navigate the mortgage process.

The MortgageAdvisorAgent specializes in:
- Mortgage education and loan program comparison
- Personalized loan selection guidance based on borrower profile
- Next-step recommendations throughout the application process
- Qualification requirements and credit guidance
- Neo4j knowledge graph integration for intelligent recommendations

Structure:
- agent.py: Main agent creation and configuration
- prompts.yaml: Co-located prompt definitions specific to mortgage guidance
- tools/: Individual tool modules for focused mortgage advisory capabilities
- tests/: Comprehensive test suite for mortgage guidance functionality
- ../shared/: Reusable utilities shared across all agents (prompt loader, etc.)

Tools (All 4 implemented - 100% data-driven from Neo4j):
- explain_loan_programs: Compare and explain different mortgage loan programs
- recommend_loan_program: Provide personalized loan recommendations  
- check_qualification_requirements: Analyze qualification requirements and identify gaps
- guide_next_steps: Provide step-by-step process guidance and preparation tips

Benefits:
- Focused mortgage expertise with deep domain knowledge
- Intelligent recommendations using Neo4j knowledge graph
- Clear separation from data collection and processing concerns
- Professional mortgage advisor experience for users
"""

from .agent import create_mortgage_advisor_agent
from .tools import (
    explain_loan_programs,
    recommend_loan_program, 
    check_qualification_requirements,
    guide_next_steps,
    get_all_mortgage_advisor_tools,
    validate_all_tools
)
from agents.shared.prompt_loader import (
    load_agent_prompt as load_mortgage_advisor_prompt,
    get_agent_prompt_loader,
    validate_agent_prompts
)

__all__ = [
    # Main agent
    "create_mortgage_advisor_agent",
    
    # All 4 implemented tools - 100% data-driven from Neo4j
    "explain_loan_programs",
    "recommend_loan_program", 
    "check_qualification_requirements",
    "guide_next_steps",
    
    # Tool management
    "get_all_mortgage_advisor_tools",
    "validate_all_tools",
    
    # Prompt management (shared utilities)
    "load_mortgage_advisor_prompt",
    "get_agent_prompt_loader",
    "validate_agent_prompts"
]
