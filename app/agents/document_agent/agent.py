"""
DocumentAgent Implementation

This agent handles mortgage document processing, validation, and workflow management
using specialized tools and Neo4j Document Verification Rules for data-driven validation.

The DocumentAgent focuses on:
- Document collection and processing workflow
- Content extraction using Neo4j business rules
- Document validation against verification rules
- Status tracking and completeness analysis
- Knowledge graph population with extracted data
"""

from typing import Dict
from langgraph.prebuilt import create_react_agent

try:
    from utils import get_llm
except ImportError:
    # Fallback for relative imports during testing
    from utils import get_llm

from utils.config import AppConfig
from .tools import get_all_document_agent_tools
from agents.shared.prompt_loader import load_agent_prompt


def create_document_agent():
    """
    Create DocumentAgent using LangGraph's prebuilt create_react_agent.
    
    This creates a specialized agent for document processing and validation using
    LangGraph's production-ready ReAct agent with focused tool integration.
    
    Features:
    - Built-in memory and state management
    - Streaming capabilities for real-time processing
    - Human-in-the-loop support for complex document reviews
    - Proper error handling and validation
    - Tool isolation for clean document processing functionality
    - Neo4j Document Verification Rules integration for data-driven validation
    
    Returns:
        Compiled LangGraph agent ready for execution
    """
    
    # Load configuration
    config = AppConfig.load()
    
    # Get centralized LLM from factory
    llm = get_llm()
    
    # Get all DocumentAgent-specific tools
    tools = get_all_document_agent_tools()
    
    # Load system prompt from YAML using shared prompt loader
    # Explicitly pass the agent directory to ensure correct path detection
    from pathlib import Path
    agent_dir = Path(__file__).parent  # Current directory (document_agent/)
    system_prompt = load_agent_prompt("document_agent", agent_dir)
    
    # Create the prebuilt ReAct agent with specialized configuration
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        name="document_agent"
    )
    
    return agent
