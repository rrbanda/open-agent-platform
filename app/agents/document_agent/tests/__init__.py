"""
DocumentAgent Test Suite

Comprehensive testing for DocumentAgent including:
- Agent creation and configuration
- Individual tool validation  
- Prompt validation
- End-to-end workflows
- Agent evaluations and performance
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path for testing
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import validation functions
try:
    from app.agents.document_agent import create_document_agent
    from app.agents.document_agent.tools import get_all_document_agent_tools
    from agents.shared.prompt_loader import load_agent_prompt
    
    def validate_document_agent_setup():
        """Validate that DocumentAgent can be created and configured properly."""
        try:
            # Test agent creation
            agent = create_document_agent()
            
            # Test tools loading
            tools = get_all_document_agent_tools()
            
            # Test prompt loading
            prompt = load_agent_prompt("document_agent")
            
            return {
                "agent_creation": agent is not None,
                "tools_loaded": len(tools) == 4,
                "prompt_loaded": len(prompt) > 100,
                "setup_complete": True
            }
        except Exception as e:
            return {
                "agent_creation": False,
                "tools_loaded": False, 
                "prompt_loaded": False,
                "setup_complete": False,
                "error": str(e)
            }
    
except ImportError as e:
    print(f"Warning: Could not import DocumentAgent components: {e}")
    
    def validate_document_agent_setup():
        return {
            "agent_creation": False,
            "tools_loaded": False,
            "prompt_loaded": False, 
            "setup_complete": False,
            "error": "Import failed"
        }

__all__ = ["validate_document_agent_setup"]
