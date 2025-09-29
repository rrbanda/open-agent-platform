"""
AppraisalAgent Implementation

This agent provides intelligent property appraisal and valuation analysis using specialized
tools and Neo4j knowledge graph integration for rule-based assessments.

The AppraisalAgent focuses on:
- Property value analysis using multiple appraisal approaches
- Comparable sales research and analysis  
- Property condition assessment for lending standards
- Appraisal report review and compliance validation
- Market conditions evaluation and impact analysis
- Knowledge graph-powered intelligent appraisal decisions
"""

from typing import Dict
from langgraph.prebuilt import create_react_agent
from pathlib import Path

try:
    from utils import get_llm
except ImportError:
    # Fallback for relative imports during testing
    from utils import get_llm

from utils.config import AppConfig
from .tools import get_all_appraisal_agent_tools
from agents.shared.prompt_loader import load_agent_prompt


def create_appraisal_agent():
    """
    Create AppraisalAgent using LangGraph's prebuilt create_react_agent.
    
    This creates a specialized agent for property appraisal and valuation analysis using
    LangGraph's production-ready ReAct agent with focused tool integration.
    
    Features:
    - Built-in memory and state management
    - Streaming capabilities for real-time analysis
    - Human-in-the-loop support for complex valuations
    - Proper error handling and validation
    - Tool isolation for clean appraisal functionality
    - Neo4j knowledge graph integration for intelligent decisions
    
    Returns:
        Compiled LangGraph agent ready for execution
    """
    
    # Load configuration
    config = AppConfig.load()
    
    # Get centralized LLM from factory
    llm = get_llm()
    
    # Get all AppraisalAgent-specific tools
    tools = get_all_appraisal_agent_tools()
    
    # Load system prompt from YAML using shared prompt loader
    # Explicitly pass the agent directory to ensure correct path detection
    agent_dir = Path(__file__).parent  # Current directory (appraisal_agent/)
    system_prompt = load_agent_prompt("appraisal_agent", agent_dir)
    
    # Create the prebuilt ReAct agent with specialized configuration
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        name="appraisal_agent"
    )
    
    return agent
