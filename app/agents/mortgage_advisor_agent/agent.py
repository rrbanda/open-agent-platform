"""
MortgageAdvisorAgent Implementation

This agent provides intelligent mortgage guidance and education using specialized
tools and Neo4j knowledge graph integration for personalized recommendations.

The MortgageAdvisorAgent focuses on:
- Mortgage education and loan program explanation
- Personalized loan selection based on borrower profile
- Qualification requirements analysis
- Next-step guidance through the mortgage process
- Knowledge graph-powered intelligent recommendations
"""

from typing import Dict
from langgraph.prebuilt import create_react_agent

try:
    from utils import get_llm
except ImportError:
    # Fallback for relative imports during testing
    from utils import get_llm

from utils.config import AppConfig
from .tools import get_all_mortgage_advisor_tools
from agents.shared.prompt_loader import load_agent_prompt


def create_mortgage_advisor_agent():
    """
    Create MortgageAdvisorAgent using LangGraph's prebuilt create_react_agent.
    
    This creates a specialized agent for mortgage guidance and education using
    LangGraph's production-ready ReAct agent with focused tool integration.
    
    Features:
    - Built-in memory and state management
    - Streaming capabilities for real-time guidance
    - Human-in-the-loop support for complex decisions
    - Proper error handling and validation
    - Tool isolation for clean mortgage advisory functionality
    - Neo4j knowledge graph integration for intelligent recommendations
    
    Returns:
        Compiled LangGraph agent ready for execution
    """
    
    # Load configuration
    config = AppConfig.load()
    
    # Get centralized LLM from factory
    llm = get_llm()
    
    # Get all MortgageAdvisorAgent-specific tools
    tools = get_all_mortgage_advisor_tools()
    
    # Load system prompt from YAML using shared prompt loader
    # Explicitly pass the agent directory to ensure correct path detection
    from pathlib import Path
    agent_dir = Path(__file__).parent  # Current directory (mortgage_advisor_agent/)
    system_prompt = load_agent_prompt("mortgage_advisor_agent", agent_dir)
    
    # Create the prebuilt ReAct agent with specialized configuration
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        name="mortgage_advisor_agent"
    )
    
    return agent
