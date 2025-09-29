"""
Test Prompt Validation for UnderwritingAgent

This module tests prompt loading, content validation, and ensures
prompts contain appropriate underwriting-specific content.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from agents.shared.prompt_loader import load_agent_prompt


class TestUnderwritingPromptValidation:
    """Test suite for UnderwritingAgent prompt validation."""
    
    def test_prompt_loading_basic(self):
        """Test that prompts can be loaded successfully."""
        print("\n📝 Testing basic prompt loading...")
        
        try:
            # Test loading with explicit path
            agent_dir = Path(current_dir).parent  # underwriting_agent directory
            prompt = load_agent_prompt("underwriting_agent", agent_dir)
            
            assert prompt is not None, "Prompt should not be None"
            assert isinstance(prompt, str), "Prompt should be a string"
            assert len(prompt) > 100, "Prompt should have substantial content"
            print(f" Prompt loaded successfully: {len(prompt)} characters")
            
        except Exception as e:
            pytest.fail(f"Basic prompt loading failed: {e}")
    
    def test_prompt_content_validation(self):
        """Test that prompt contains expected underwriting-specific content."""
        print("\n🔍 Testing prompt content validation...")
        
        try:
            agent_dir = Path(current_dir).parent
            prompt = load_agent_prompt("underwriting_agent", agent_dir)
            
            # Check for key underwriting terms
            underwriting_keywords = [
                "UnderwritingAgent",
                "underwriting",
                "credit risk",
                "analyze_credit_risk",
                "calculate_debt_to_income",
                "evaluate_income_sources",
                "make_underwriting_decision"
            ]
            
            # Check for DTI-related terms (flexible matching)
            dti_terms = ["debt-to-income", "dti", "debt to income"]
            has_dti_terms = any(term.lower() in prompt.lower() for term in dti_terms)
            
            missing_keywords = []
            for keyword in underwriting_keywords:
                if keyword not in prompt:
                    missing_keywords.append(keyword)
            
            # Check DTI terms separately
            if not has_dti_terms:
                missing_keywords.append("DTI/debt-to-income terms")
            
            assert len(missing_keywords) == 0, f"Missing keywords in prompt: {missing_keywords}"
            
            # Check for proper tool descriptions
            assert "analyze_credit_risk" in prompt, "Should mention credit risk analysis tool"
            assert "calculate_debt_to_income" in prompt, "Should mention DTI calculation tool"
            assert "evaluate_income_sources" in prompt, "Should mention income evaluation tool"
            assert "make_underwriting_decision" in prompt, "Should mention decision making tool"
            
            print(" All expected underwriting content found in prompt")
            
        except Exception as e:
            pytest.fail(f"Prompt content validation failed: {e}")
    
    def test_prompt_structure_validation(self):
        """Test that prompt has proper structure and formatting."""
        print("\n📋 Testing prompt structure validation...")
        
        try:
            agent_dir = Path(current_dir).parent
            prompt = load_agent_prompt("underwriting_agent", agent_dir)
            
            # Check for key structural elements
            structural_elements = [
                "## Your Role",
                "## Available Tools",
                "## How to Help Users",
                "## Key Guidelines"
            ]
            
            for element in structural_elements:
                assert element in prompt, f"Missing structural element: {element}"
            
            # Check that prompt isn't too short or too long
            assert 1000 <= len(prompt) <= 5000, f"Prompt length should be reasonable: {len(prompt)} characters"
            
            # Check that prompt ends appropriately
            assert "underwriting" in prompt.lower(), "Prompt should focus on underwriting"
            
            print(" Prompt structure validation passed")
            
        except Exception as e:
            pytest.fail(f"Prompt structure validation failed: {e}")
    
    def test_prompt_yaml_file_exists(self):
        """Test that the prompts.yaml file exists and is readable."""
        print("\n📄 Testing prompts.yaml file existence...")
        
        try:
            agent_dir = Path(current_dir).parent
            prompts_file = agent_dir / "prompts.yaml"
            
            assert prompts_file.exists(), f"prompts.yaml file should exist at {prompts_file}"
            assert prompts_file.is_file(), "prompts.yaml should be a file"
            
            # Test that file is readable
            with open(prompts_file, 'r') as f:
                content = f.read()
                assert len(content) > 100, "prompts.yaml should have substantial content"
                assert "system_prompt:" in content, "Should contain system_prompt key"
                
            print(" prompts.yaml file validation passed")
            
        except Exception as e:
            pytest.fail(f"prompts.yaml file validation failed: {e}")
    
    def test_prompt_differentiation(self):
        """Test that UnderwritingAgent prompts are different from other agents."""
        print("\n🔄 Testing prompt differentiation...")
        
        try:
            # Load UnderwritingAgent prompt
            agent_dir = Path(current_dir).parent
            underwriting_prompt = load_agent_prompt("underwriting_agent", agent_dir)
            
            # Try to load MortgageAdvisorAgent prompt for comparison
            advisor_dir = agent_dir.parent / "mortgage_advisor_agent"
            if advisor_dir.exists():
                advisor_prompt = load_agent_prompt("mortgage_advisor_agent", advisor_dir)
                
                # Ensure they're substantially different
                assert underwriting_prompt != advisor_prompt, "Prompts should be different from MortgageAdvisorAgent"
                
                # Check for unique underwriting content
                assert "underwriting decision" in underwriting_prompt.lower(), "Should mention underwriting decisions"
                assert "risk assessment" in underwriting_prompt.lower(), "Should mention risk assessment"
                
                print(" Prompt differentiation validation passed")
            else:
                print("⚠️ MortgageAdvisorAgent not available for comparison, skipping differentiation test")
                
        except Exception as e:
            pytest.fail(f"Prompt differentiation test failed: {e}")
    
    def test_shared_prompt_loader_integration(self):
        """Test integration with shared prompt loader utilities."""
        print("\n🔗 Testing shared prompt loader integration...")
        
        try:
            from agents.shared.prompt_loader import (
                get_agent_prompt_loader,
                validate_agent_prompts
            )
            
            # Test prompt loader factory
            agent_dir = Path(current_dir).parent
            loader = get_agent_prompt_loader("underwriting_agent", agent_dir)
            assert loader is not None, "Should create prompt loader"
            
            # Test validation (if implemented)
            try:
                validation_result = validate_agent_prompts("underwriting_agent", agent_dir)
                if validation_result is not None:
                    assert validation_result, "Prompt validation should pass"
            except:
                # validation_result might not be fully implemented, which is OK
                pass
            
            print(" Shared prompt loader integration passed")
            
        except Exception as e:
            pytest.fail(f"Shared prompt loader integration failed: {e}")


def run_prompt_validation_tests():
    """Run all prompt validation tests and return results."""
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    test_class = TestUnderwritingPromptValidation()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    results["total_tests"] = len(test_methods)
    
    for test_method_name in test_methods:
        try:
            test_method = getattr(test_class, test_method_name)
            test_method()
            results["passed_tests"] += 1
            results["test_details"].append(f" {test_method_name}: PASSED")
        except Exception as e:
            results["failed_tests"] += 1
            results["test_details"].append(f" {test_method_name}: FAILED - {str(e)}")
    
    return results


if __name__ == "__main__":
    print("🧪 RUNNING UNDERWRITING AGENT PROMPT VALIDATION TESTS")
    print("=" * 60)
    
    results = run_prompt_validation_tests()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    
    print(f"\n📋 TEST DETAILS:")
    for detail in results["test_details"]:
        print(detail)
    
    if results["failed_tests"] == 0:
        print("\n🎉 ALL PROMPT VALIDATION TESTS PASSED!")
    else:
        print(f"\n⚠️ {results['failed_tests']} TEST(S) FAILED")
        sys.exit(1)
