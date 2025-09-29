"""
ApplicationAgent Prompt Validation Tests

This module tests the ApplicationAgent's prompt loading, content validation,
and YAML structure to ensure proper agent behavior and guidance.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

try:
    from agents.shared.prompt_loader import load_agent_prompt
    import yaml
    
    print("📝 Testing ApplicationAgent Prompt Validation...")
    
    # Test 1: Prompt loading functionality
    print("\n1. Testing prompt loading...")
    agent_dir = current_dir.parent  # application_agent directory
    prompt = load_agent_prompt("application_agent", agent_dir)
    assert prompt is not None, "Prompt should be loaded successfully"
    assert len(prompt.strip()) > 0, "Prompt should have content"
    print("    Prompt loaded successfully")
    
    # Test 2: YAML structure validation
    print("\n2. Testing YAML structure...")
    prompt_file = agent_dir / "prompts.yaml"
    assert prompt_file.exists(), "prompts.yaml file should exist"
    
    with open(prompt_file, 'r') as f:
        prompt_data = yaml.safe_load(f)
    
    assert isinstance(prompt_data, dict), "Prompt file should contain a dictionary"
    assert "system_prompt" in prompt_data, "Prompt file should have system_prompt key"
    print("    YAML structure is valid")
    
    # Test 3: Prompt content validation
    print("\n3. Testing prompt content...")
    system_prompt = prompt_data["system_prompt"]
    assert len(system_prompt.strip()) > 100, "System prompt should have substantial content"
    
    # Check for key ApplicationAgent concepts
    required_keywords = [
        "ApplicationAgent",
        "application intake",
        "workflow coordination",
        "receive_mortgage_application",
        "check_application_completeness", 
        "perform_initial_qualification",
        "track_application_status"
    ]
    
    missing_keywords = []
    for keyword in required_keywords:
        if keyword not in system_prompt:
            missing_keywords.append(keyword)
    
    assert len(missing_keywords) == 0, f"Missing keywords in prompt: {missing_keywords}"
    print("    All required keywords present in prompt")
    
    # Test 4: Tool descriptions validation
    print("\n4. Testing tool descriptions...")
    tool_keywords = [
        "application intake",
        "completeness",
        "qualification",
        "routing",
        "status tracking"
    ]
    
    found_tools = 0
    for tool_keyword in tool_keywords:
        if tool_keyword in system_prompt:
            found_tools += 1
    
    assert found_tools >= 4, f"Should find descriptions for most tools, found {found_tools}/{len(tool_keywords)}"
    print("    Tool descriptions present in prompt")
    
    # Test 5: Agent role and behavior validation
    print("\n5. Testing agent role definition...")
    role_keywords = [
        "mortgage application",
        "intake specialist", 
        "workflow",
        "professional"
    ]
    
    role_found = 0
    for role_keyword in role_keywords:
        if role_keyword in system_prompt.lower():
            role_found += 1
    
    assert role_found >= 2, f"Should define agent role clearly, found {role_found}/{len(role_keywords)} role indicators"
    print("    Agent role clearly defined")
    
    # Test 6: Neo4j and data-driven approach validation
    print("\n6. Testing data-driven approach references...")
    data_driven_keywords = [
        "Neo4j",
        "data-driven", 
        "rules",
        "tools"
    ]
    
    data_driven_found = 0
    for keyword in data_driven_keywords:
        if keyword in system_prompt:
            data_driven_found += 1
    
    assert data_driven_found >= 2, f"Should reference data-driven approach, found {data_driven_found}/{len(data_driven_keywords)}"
    print("    Data-driven approach properly referenced")
    
    # Test 7: Workflow integration validation
    print("\n7. Testing workflow integration references...")
    workflow_keywords = [
        "MortgageAdvisorAgent",
        "DocumentAgent",
        "AppraisalAgent", 
        "UnderwritingAgent",
        "agent"
    ]
    
    workflow_found = 0
    for keyword in workflow_keywords:
        if keyword in system_prompt:
            workflow_found += 1
    
    assert workflow_found >= 3, f"Should reference other agents in workflow, found {workflow_found}/{len(workflow_keywords)}"
    print("    Workflow integration properly described")
    
    print("\n🎉 All prompt validation tests passed!")
    
except Exception as e:
    print(f"\n Prompt validation test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def run_prompt_validation_tests():
    """
    Run ApplicationAgent prompt validation tests and return success status.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        # Get the agent directory
        current_test_dir = Path(__file__).parent
        agent_dir = current_test_dir.parent
        
        # Test prompt loading
        prompt = load_agent_prompt("application_agent", agent_dir)
        if not prompt or len(prompt.strip()) < 50:
            return False
        
        # Test YAML structure
        prompt_file = agent_dir / "prompts.yaml"
        if not prompt_file.exists():
            return False
        
        with open(prompt_file, 'r') as f:
            prompt_data = yaml.safe_load(f)
        
        if not isinstance(prompt_data, dict) or "system_prompt" not in prompt_data:
            return False
        
        # Test key content presence
        system_prompt = prompt_data["system_prompt"]
        essential_keywords = ["ApplicationAgent", "application intake", "tools"]
        
        for keyword in essential_keywords:
            if keyword not in system_prompt:
                return False
        
        return True
        
    except Exception as e:
        print(f"Prompt validation test error: {e}")
        return False


if __name__ == "__main__":
    # When run directly, execute the tests
    pass
