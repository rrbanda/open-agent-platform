"""
AppraisalAgent - Intelligent Property Appraisal and Valuation Analysis

This agent provides comprehensive property appraisal analysis and valuation decisions
using specialized tools and Neo4j knowledge graph integration for rule-based assessments.

The AppraisalAgent specializes in:
- Property value analysis using multiple appraisal approaches (sales comparison, cost, income)
- Comparable sales research and adjustment analysis
- Property condition assessment for lending standards
- Appraisal report review and compliance validation
- Market conditions evaluation and impact analysis
- Neo4j knowledge graph integration for rule-driven appraisal decisions

Structure:
- agent.py: Main agent creation and configuration
- prompts.yaml: Co-located prompt definitions specific to property appraisal
- tools/: Individual tool modules for focused appraisal capabilities
- tests/: Comprehensive test suite for appraisal functionality
- ../shared/: Reusable utilities shared across all agents (prompt loader, etc.)

Tools (All 5 implemented - 100% data-driven from Neo4j):
- analyze_property_value: Comprehensive property valuation using multiple approaches
- find_comparable_sales: Comparable sales research with adjustment analysis
- assess_property_condition: Property condition evaluation for lending standards
- review_appraisal_report: Appraisal report compliance and quality review
- evaluate_market_conditions: Market analysis and valuation impact assessment

Benefits:
- Focused appraisal expertise with deep property valuation knowledge
- Intelligent, rule-based valuations using Neo4j knowledge graph
- Clear separation from mortgage guidance and document processing concerns
- Professional and consistent appraisal analysis
"""

from .agent import create_appraisal_agent
from .tools import (
    analyze_property_value,
    find_comparable_sales,
    assess_property_condition,
    review_appraisal_report,
    evaluate_market_conditions,
    get_all_appraisal_agent_tools,
    validate_all_tools
)
from agents.shared.prompt_loader import (
    load_agent_prompt as load_appraisal_prompt,
    get_agent_prompt_loader,
    validate_agent_prompts
)

__all__ = [
    # Main agent
    "create_appraisal_agent",
    
    # All 5 implemented tools - 100% data-driven from Neo4j
    "analyze_property_value",
    "find_comparable_sales",
    "assess_property_condition",
    "review_appraisal_report",
    "evaluate_market_conditions",
    
    # Tool management
    "get_all_appraisal_agent_tools",
    "validate_all_tools",
    
    # Prompt management (shared utilities)
    "load_appraisal_prompt",
    "get_agent_prompt_loader",
    "validate_agent_prompts"
]
