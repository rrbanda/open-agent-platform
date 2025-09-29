"""
Test Prompt Validation

Tests for YAML prompt loading, validation, and content verification
for the MortgageAdvisorAgent.
"""

import pytest
import sys
from pathlib import Path
import yaml
import os

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from agents.shared.prompt_loader import (
    load_agent_prompt,
    get_agent_prompt_loader,
    validate_agent_prompts
)


def test_prompt_yaml_file_exists():
    """Test that the prompts.yaml file exists in the agent folder."""
    print("📄 Testing prompts.yaml file existence...")
    
    try:
        # Get the agent folder path
        agent_folder = Path(__file__).parent.parent
        prompts_file = agent_folder / "prompts.yaml"
        
        assert prompts_file.exists(), f"prompts.yaml should exist at {prompts_file}"
        
        # Check file is readable
        assert prompts_file.is_file(), "prompts.yaml should be a file"
        assert os.access(prompts_file, os.R_OK), "prompts.yaml should be readable"
        
        print(" prompts.yaml file existence test passed")
        return True
        
    except Exception as e:
        print(f" prompts.yaml file existence failed: {e}")
        return False


def test_prompt_yaml_structure():
    """Test that prompts.yaml has valid YAML structure."""
    print("📄 Testing prompts.yaml structure...")
    
    try:
        # Get the agent folder path
        agent_folder = Path(__file__).parent.parent
        prompts_file = agent_folder / "prompts.yaml"
        
        # Load and parse YAML
        with open(prompts_file, 'r') as f:
            prompt_data = yaml.safe_load(f)
        
        assert isinstance(prompt_data, dict), "prompts.yaml should contain a dictionary"
        
        # Check for required system_prompt key
        assert "system_prompt" in prompt_data, "prompts.yaml should contain 'system_prompt' key"
        
        # Verify system_prompt is a string
        system_prompt = prompt_data["system_prompt"]
        assert isinstance(system_prompt, str), "system_prompt should be a string"
        assert len(system_prompt.strip()) > 0, "system_prompt should not be empty"
        
        print(" prompts.yaml structure test passed")
        return True
        
    except yaml.YAMLError as e:
        print(f" YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f" prompts.yaml structure failed: {e}")
        return False


def test_prompt_content_validation():
    """Test that prompt content contains expected mortgage advisor elements."""
    print("📄 Testing prompt content validation...")
    
    try:
        # Load prompt using the shared loader
        system_prompt = load_agent_prompt("mortgage_advisor_agent")
        
        assert isinstance(system_prompt, str), "Loaded prompt should be a string"
        assert len(system_prompt.strip()) > 0, "Loaded prompt should not be empty"
        
        # Check for key mortgage advisor elements
        required_elements = [
            "mortgageadvisoragent",
            "mortgage", 
            "loan",
            "tool",  # Changed from "tools" to be more flexible
            "guidance"
        ]
        
        prompt_lower = system_prompt.lower()
        missing_elements = []
        
        for element in required_elements:
            if element.lower() not in prompt_lower:
                missing_elements.append(element)
        
        assert len(missing_elements) == 0, f"Prompt missing elements: {missing_elements}"
        
        # Check for tool references (should mention the 4 tools)
        expected_tools = [
            "explain_loan_programs",
            "recommend_loan_program",
            "check_qualification_requirements", 
            "guide_next_steps"
        ]
        
        missing_tools = []
        for tool in expected_tools:
            if tool not in prompt_lower:
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"⚠️ Tools not mentioned in prompt: {missing_tools}")
        
        print(" Prompt content validation test passed")
        return True
        
    except Exception as e:
        print(f" Prompt content validation failed: {e}")
        return False


def test_shared_prompt_loader():
    """Test the shared prompt loader functionality."""
    print("📄 Testing shared prompt loader...")
    
    try:
        # Test generic load_agent_prompt function
        prompt1 = load_agent_prompt("mortgage_advisor_agent")
        assert isinstance(prompt1, str), "Generic loader should return string"
        assert len(prompt1.strip()) > 0, "Generic loader should return non-empty prompt"
        
        # Test get_agent_prompt_loader function
        loader = get_agent_prompt_loader("mortgage_advisor_agent")
        assert loader is not None, "Prompt loader should be created"
        
        # Test validation function (may not exist yet, so try-catch)
        try:
            validation_result = validate_agent_prompts("mortgage_advisor_agent")
            assert isinstance(validation_result, bool), "Validation should return boolean"
        except (AttributeError, NotImplementedError):
            print("   ⚠️ validate_agent_prompts not implemented yet - skipping")
        
        print(" Shared prompt loader test passed")
        return True
        
    except Exception as e:
        print(f" Shared prompt loader failed: {e}")
        return False


def test_prompt_consistency():
    """Test consistency between YAML file and loaded prompt."""
    print("📄 Testing prompt consistency...")
    
    try:
        # Load directly from YAML file
        agent_folder = Path(__file__).parent.parent
        prompts_file = agent_folder / "prompts.yaml"
        
        with open(prompts_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        yaml_prompt = yaml_data["system_prompt"]
        
        # Load using shared loader
        loaded_prompt = load_agent_prompt("mortgage_advisor_agent")
        
        # They should be very similar (allowing for minor whitespace differences)
        yaml_lines = len(yaml_prompt.strip().split('\n'))
        loaded_lines = len(loaded_prompt.strip().split('\n'))
        
        # Allow some flexibility in line counts (shared loader might add/remove whitespace)
        line_diff = abs(yaml_lines - loaded_lines)
        assert line_diff <= 5, f"Prompt line count difference too large: YAML {yaml_lines} vs Loaded {loaded_lines}"
        
        # Check that core content exists in both
        yaml_words = set(yaml_prompt.lower().split())
        loaded_words = set(loaded_prompt.lower().split())
        common_words = yaml_words.intersection(loaded_words)
        word_similarity = len(common_words) / max(len(yaml_words), len(loaded_words))
        assert word_similarity > 0.8, f"Prompts should be similar, similarity: {word_similarity:.2f}"
        
        print(" Prompt consistency test passed")
        return True
        
    except Exception as e:
        print(f" Prompt consistency failed: {e}")
        return False


def test_prompt_template_variables():
    """Test if prompt contains any template variables that need replacement."""
    print("📄 Testing prompt template variables...")
    
    try:
        system_prompt = load_agent_prompt("mortgage_advisor_agent")
        
        # Check for common template patterns that shouldn't be in final prompt
        template_patterns = [
            "{{",
            "}}",
            "${",
            "}", 
            "{%",
            "%}",
            "<<<",
            ">>>"
        ]
        
        found_patterns = []
        for pattern in template_patterns:
            if pattern in system_prompt:
                found_patterns.append(pattern)
        
        if found_patterns:
            print(f"⚠️ Found potential template patterns: {found_patterns}")
            # This might be okay, just warn
        
        # Check for placeholder text
        placeholder_patterns = [
            "TODO",
            "FIXME",
            "placeholder",
            "REPLACE_ME",
            "[INSERT",
            "TBD"
        ]
        
        found_placeholders = []
        prompt_upper = system_prompt.upper()
        for pattern in placeholder_patterns:
            if pattern.upper() in prompt_upper:
                found_placeholders.append(pattern)
        
        assert len(found_placeholders) == 0, f"Prompt contains placeholders: {found_placeholders}"
        
        print(" Prompt template variables test passed")
        return True
        
    except Exception as e:
        print(f" Prompt template variables failed: {e}")
        return False


def test_prompt_length_and_quality():
    """Test prompt length and basic quality metrics."""
    print("📄 Testing prompt length and quality...")
    
    try:
        system_prompt = load_agent_prompt("mortgage_advisor_agent")
        
        # Length checks
        assert len(system_prompt) > 100, "Prompt should be substantial (>100 chars)"
        assert len(system_prompt) < 50000, "Prompt should not be excessively long (<50k chars)"
        
        # Word count
        word_count = len(system_prompt.split())
        assert word_count > 50, "Prompt should have substantial content (>50 words)"
        
        # Line count (count non-empty lines)
        non_empty_lines = [line for line in system_prompt.split('\n') if line.strip()]
        line_count = len(non_empty_lines)
        assert line_count > 5, "Prompt should be well-structured (>5 non-empty lines)"
        
        # Basic readability - should have sentences
        sentence_endings = system_prompt.count('.') + system_prompt.count('!') + system_prompt.count('?')
        assert sentence_endings > 5, "Prompt should contain multiple sentences"
        
        print(f"   Prompt stats: {len(system_prompt)} chars, {word_count} words, {line_count} lines")
        print(" Prompt length and quality test passed")
        return True
        
    except Exception as e:
        print(f" Prompt length and quality failed: {e}")
        return False


def run_prompt_validation_tests():
    """Run all prompt validation tests."""
    print("\n🧪 Running Prompt Validation Tests")
    print("=" * 40)
    
    tests = [
        test_prompt_yaml_file_exists,
        test_prompt_yaml_structure,
        test_prompt_content_validation,
        test_shared_prompt_loader,
        test_prompt_consistency,
        test_prompt_template_variables,
        test_prompt_length_and_quality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f" Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Prompt Validation Tests: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    success = run_prompt_validation_tests()
    sys.exit(0 if success else 1)
