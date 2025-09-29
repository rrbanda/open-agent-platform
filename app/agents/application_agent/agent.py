"""
ApplicationAgent Implementation

This agent provides intelligent mortgage application intake and workflow coordination
using specialized tools and Neo4j knowledge graph integration for rule-based processing.

The ApplicationAgent focuses on:
- Mortgage application intake and validation
- Application completeness verification
- Initial qualification assessment and pre-screening
- Workflow routing coordination across agents  
- Application status tracking and management
- Knowledge graph-powered intelligent application decisions
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
from .tools import get_all_application_agent_tools
from agents.shared.prompt_loader import load_agent_prompt


def create_application_agent():
    """
    Create ApplicationAgent using LangGraph's prebuilt create_react_agent.
    
    This creates a specialized agent for mortgage application intake and workflow coordination
    using LangGraph's production-ready ReAct agent with focused tool integration.
    
    Features:
    - Built-in memory and state management
    - Streaming capabilities for real-time processing
    - Human-in-the-loop support for complex applications
    - Proper error handling and validation
    - Tool isolation for clean application management functionality
    - Neo4j knowledge graph integration for intelligent decisions
    
    Returns:
        Compiled LangGraph agent ready for execution
    """
    
    # Load configuration
    config = AppConfig.load()
    
    # Get centralized LLM from factory
    llm = get_llm()
    
    # Get all ApplicationAgent-specific tools
    tools = get_all_application_agent_tools()
    
    # Load system prompt from YAML using shared prompt loader
    # Explicitly pass the agent directory to ensure correct path detection
    agent_dir = Path(__file__).parent  # Current directory (application_agent/)
    system_prompt = load_agent_prompt("application_agent", agent_dir)
    
    # Create the prebuilt ReAct agent with specialized configuration
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        name="application_agent"
    )
    
    return agent
