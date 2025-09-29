"""
UnderwritingAgent - Intelligent Mortgage Underwriting and Decision Making

This agent provides comprehensive mortgage underwriting analysis and makes lending
decisions based on risk assessment and regulatory guidelines.

The UnderwritingAgent specializes in:
- Credit risk analysis and evaluation using comprehensive underwriting rules
- Debt-to-income calculations and validation against program requirements
- Income source evaluation and qualification determination
- Final underwriting decisions with detailed reasoning and conditions
- Neo4j knowledge graph integration for rule-based decision making

Structure:
- agent.py: Main agent creation and configuration
- prompts.yaml: Co-located prompt definitions specific to underwriting decisions
- tools/: Individual tool modules for focused underwriting capabilities
- tests/: Comprehensive test suite for underwriting functionality
- ../shared/: Reusable utilities shared across all agents (prompt loader, etc.)

Tools (All 4 implemented - 100% data-driven from Neo4j):
- analyze_credit_risk: Comprehensive credit risk assessment using underwriting rules
- calculate_debt_to_income: DTI calculations and validation against program limits
- evaluate_income_sources: Income source analysis and qualification calculations
- make_underwriting_decision: Final underwriting decisions with detailed reasoning

Benefits:
- Professional underwriting expertise with comprehensive risk analysis
- Rule-based decisions using Neo4j underwriting knowledge graph
- Clear separation from application processing and customer interaction
- Automated decision making with manual review triggers for complex cases
"""

from .agent import create_underwriting_agent
from .tools import (
    analyze_credit_risk,
    calculate_debt_to_income, 
    evaluate_income_sources,
    make_underwriting_decision,
    get_all_underwriting_agent_tools,
    validate_all_tools
)
from agents.shared.prompt_loader import (
    load_agent_prompt as load_underwriting_agent_prompt,
    get_agent_prompt_loader,
    validate_agent_prompts
)

__all__ = [
    # Main agent
    "create_underwriting_agent",
    
    # All 4 implemented tools - 100% data-driven from Neo4j
    "analyze_credit_risk",
    "calculate_debt_to_income", 
    "evaluate_income_sources",
    "make_underwriting_decision",
    
    # Tool management
    "get_all_underwriting_agent_tools",
    "validate_all_tools",
    
    # Prompt management (shared utilities)
    "load_underwriting_agent_prompt",
    "get_agent_prompt_loader",
    "validate_agent_prompts"
]
