"""
UnderwritingAgent Implementation

This agent provides intelligent mortgage underwriting decisions using specialized
tools and Neo4j knowledge graph integration for comprehensive risk assessment.

The UnderwritingAgent focuses on:
- Credit risk analysis and evaluation
- Debt-to-income calculations and validation
- Income source evaluation and qualification
- Final underwriting decision making
- Knowledge graph-powered underwriting rules application
"""

from typing import Dict
from langgraph.prebuilt import create_react_agent

try:
    from utils import get_llm
except ImportError:
    # Fallback for relative imports during testing
    from utils import get_llm

from utils.config import AppConfig
from .tools import get_all_underwriting_agent_tools
from agents.shared.prompt_loader import load_agent_prompt


def create_underwriting_agent():
    """
    Create UnderwritingAgent using LangGraph's prebuilt create_react_agent.
    
    This creates a specialized agent for mortgage underwriting decisions using
    LangGraph's production-ready ReAct agent with focused tool integration.
    
    Features:
    - Built-in memory and state management
    - Streaming capabilities for real-time underwriting
    - Human-in-the-loop support for complex decisions
    - Proper error handling and validation
    - Tool isolation for clean underwriting functionality
    - Neo4j knowledge graph integration for rule-based decisions
    
    Returns:
        Compiled LangGraph agent ready for execution
    """
    
    # Load configuration
    config = AppConfig.load()
    
    # Get centralized LLM from factory
    llm = get_llm()
    
    # Get all UnderwritingAgent-specific tools
    tools = get_all_underwriting_agent_tools()
    
    # Load system prompt from YAML using shared prompt loader
    # Explicitly pass the agent directory to ensure correct path detection
    from pathlib import Path
    agent_dir = Path(__file__).parent  # Current directory (underwriting_agent/)
    system_prompt = load_agent_prompt("underwriting_agent", agent_dir)
    
    # Create the prebuilt ReAct agent with specialized configuration
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        name="underwriting_agent"
    )
    
    return agent
