"""
Generic Agent Prompt Loader

This module provides a reusable prompt loading system that can be used by any agent.
It supports local prompts.yaml files co-located with agents and falls back to
centralized prompt loading when needed.

Benefits:
- Consistent prompt loading across all agents
- Local prompt files for better maintainability 
- Automatic fallback to centralized system
- Reduced code duplication
- Easy integration for new agents
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


class AgentPromptLoader:
    """Generic prompt loader that can be used by any agent."""
    
    def __init__(self, agent_name: str, agent_dir: Optional[Path] = None):
        """
        Initialize the prompt loader for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., "data_agent", "application_agent")
            agent_dir: Directory containing the agent (auto-detected if None)
        """
        self.agent_name = agent_name
        
        if agent_dir is None:
            # Try to auto-detect agent directory from call stack
            import inspect
            caller_frame = inspect.currentframe().f_back
            caller_file = caller_frame.f_code.co_filename
            self.agent_dir = Path(caller_file).parent
        else:
            self.agent_dir = Path(agent_dir)
        
        self.local_prompts_file = self.agent_dir / "prompts.yaml"
    
    @lru_cache(maxsize=1)
    def load_prompts(self) -> Dict[str, Any]:
        """
        Load prompts for the agent with fallback to centralized loader.
        
        Returns:
            Dict containing all prompts for the agent
        """
        # Try to load from local file first
        if self.local_prompts_file.exists():
            try:
                with open(self.local_prompts_file, 'r', encoding='utf-8') as f:
                    prompts = yaml.safe_load(f)
                    if prompts:
                        return prompts
            except Exception as e:
                print(f"Warning: Failed to load local prompts from {self.local_prompts_file}: {e}")
        
        # Fallback to centralized prompt loader
        try:
            from ...prompt_loader import get_prompt_loader
            centralized_loader = get_prompt_loader()
            
            # Map agent names to centralized loader methods
            loader_methods = {
                "data_agent": centralized_loader.get_data_agent_prompts,
                "property_agent": centralized_loader.get_property_agent_prompts,
                "underwriting_agent": centralized_loader.get_underwriting_agent_prompts,
                "compliance_agent": centralized_loader.get_compliance_agent_prompts,
                "closing_agent": centralized_loader.get_closing_agent_prompts,
                "customer_service_agent": centralized_loader.get_customer_service_agent_prompts,
                "application_agent": centralized_loader.get_application_agent_prompts,
                "document_agent": centralized_loader.get_document_agent_prompts
            }
            
            if self.agent_name in loader_methods:
                return loader_methods[self.agent_name]()
            else:
                print(f"Warning: No centralized loader method for {self.agent_name}")
                
        except Exception as e:
            print(f"Warning: Failed to load centralized prompts: {e}")
        
        # Return minimal default prompt as last resort
        return self._get_default_prompts()
    
    def get_system_prompt(self) -> str:
        """
        Get the main system prompt for the agent.
        
        Returns:
            String containing the system prompt
        """
        prompts = self.load_prompts()
        return prompts.get("system_prompt", self._get_default_system_prompt())
    
    def get_prompt_section(self, section_name: str) -> str:
        """
        Get a specific prompt section.
        
        Args:
            section_name: Name of the prompt section
            
        Returns:
            String containing the prompt section content
        """
        prompts = self.load_prompts()
        return prompts.get(section_name, "")
    
    def get_all_sections(self) -> Dict[str, str]:
        """
        Get all prompt sections as a dictionary.
        
        Returns:
            Dict mapping section names to their content
        """
        prompts = self.load_prompts()
        # Filter out non-string values to get only prompt sections
        return {k: v for k, v in prompts.items() if isinstance(v, str)}
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """
        Get minimal default prompts as fallback.
        
        Returns:
            Dict with minimal default prompts
        """
        return {
            "system_prompt": self._get_default_system_prompt(),
            "instructions": f"You are a {self.agent_name.replace('_', ' ').title()} that helps with mortgage processing.",
            "final_response_instructions": "Provide complete, helpful responses to user questions."
        }
    
    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt as last resort fallback.
        
        Returns:
            String containing minimal system prompt
        """
        agent_title = self.agent_name.replace('_', ' ').title()
        return f"""You are a {agent_title} that assists with mortgage processing and customer service.

Your role is to help users with mortgage-related tasks using your specialized tools and knowledge.

Instructions:
- Use your available tools to provide helpful assistance
- Be professional, friendly, and informative
- Focus on providing accurate and actionable guidance
- Always aim to help users achieve their mortgage goals"""


# Global cache for prompt loaders to avoid recreation
_prompt_loaders: Dict[str, AgentPromptLoader] = {}


def get_agent_prompt_loader(agent_name: str, agent_dir: Optional[Path] = None) -> AgentPromptLoader:
    """
    Get a prompt loader for the specified agent.
    
    Args:
        agent_name: Name of the agent
        agent_dir: Directory containing the agent (auto-detected if None)
        
    Returns:
        AgentPromptLoader instance for the agent
    """
    cache_key = f"{agent_name}_{agent_dir}" if agent_dir else agent_name
    
    if cache_key not in _prompt_loaders:
        # Auto-detect agent directory if not provided
        if agent_dir is None:
            import inspect
            caller_frame = inspect.currentframe().f_back
            caller_file = caller_frame.f_code.co_filename
            agent_dir = Path(caller_file).parent
        
        _prompt_loaders[cache_key] = AgentPromptLoader(agent_name, agent_dir)
    
    return _prompt_loaders[cache_key]


def load_agent_prompt(agent_name: str, agent_dir: Optional[Path] = None) -> str:
    """
    Load the main system prompt for any agent.
    
    This is the main convenience function that agents should use.
    
    Args:
        agent_name: Name of the agent (e.g., "data_agent")
        agent_dir: Directory containing the agent (auto-detected if None)
        
    Returns:
        String containing the system prompt
    """
    loader = get_agent_prompt_loader(agent_name, agent_dir)
    return loader.get_system_prompt()


def validate_agent_prompts(agent_name: str, agent_dir: Optional[Path] = None) -> Dict[str, bool]:
    """
    Validate that agent prompts are properly loaded.
    
    Args:
        agent_name: Name of the agent
        agent_dir: Directory containing the agent (auto-detected if None)
        
    Returns:
        Dict mapping validation checks to their status
    """
    validation_results = {}
    
    try:
        loader = get_agent_prompt_loader(agent_name, agent_dir)
        
        # Test loading system prompt
        system_prompt = loader.get_system_prompt()
        validation_results["system_prompt"] = isinstance(system_prompt, str) and len(system_prompt) > 100
        
        # Test loading all sections
        all_sections = loader.get_all_sections()
        validation_results["sections_loaded"] = len(all_sections) > 0
        
        # Test that local file exists (if expected)
        local_file_exists = loader.local_prompts_file.exists()
        validation_results["local_file_exists"] = local_file_exists
        
        # Test prompt content quality
        if system_prompt:
            validation_results["prompt_mentions_agent"] = agent_name.replace('_', '').lower() in system_prompt.lower()
            validation_results["prompt_has_instructions"] = "instruction" in system_prompt.lower()
        
    except Exception as e:
        print(f"Validation error for {agent_name}: {e}")
        validation_results["validation_error"] = False
    
    return validation_results


# Convenience functions for specific agents


def load_data_agent_prompt(agent_dir: Optional[Path] = None) -> str:
    """Load DataAgent prompt."""
    return load_agent_prompt("data_agent", agent_dir)


def load_property_agent_prompt(agent_dir: Optional[Path] = None) -> str:
    """Load AppraisalAgent prompt."""
    return load_agent_prompt("property_agent", agent_dir)


def load_underwriting_agent_prompt(agent_dir: Optional[Path] = None) -> str:
    """Load UnderwritingAgent prompt.""" 
    return load_agent_prompt("underwriting_agent", agent_dir)


def load_compliance_agent_prompt(agent_dir: Optional[Path] = None) -> str:
    """Load ComplianceAgent prompt."""
    return load_agent_prompt("compliance_agent", agent_dir)


def load_closing_agent_prompt(agent_dir: Optional[Path] = None) -> str:
    """Load ClosingAgent prompt."""
    return load_agent_prompt("closing_agent", agent_dir)


def load_customer_service_agent_prompt(agent_dir: Optional[Path] = None) -> str:
    """Load CustomerServiceAgent prompt."""
    return load_agent_prompt("customer_service_agent", agent_dir)


def load_application_agent_prompt(agent_dir: Optional[Path] = None) -> str:
    """Load ApplicationAgent prompt."""
    return load_agent_prompt("application_agent", agent_dir)


def load_document_agent_prompt(agent_dir: Optional[Path] = None) -> str:
    """Load DocumentAgent prompt."""
    return load_agent_prompt("document_agent", agent_dir)
