"""
Test End-to-End Workflows for UnderwritingAgent

This module tests complete agent workflows from user input to final response,
ensuring the agent behaves correctly in realistic underwriting scenarios.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from app.agents.underwriting_agent import create_underwriting_agent


def _extract_message_content(msg):
    """Helper function to extract content from different message formats."""
    if hasattr(msg, 'content'):
        return msg.content
    elif isinstance(msg, dict) and 'content' in msg:
        return msg['content']
    else:
        return str(msg)


def _get_message_role(msg):
    """Helper function to get role from different message formats."""
    if hasattr(msg, 'type'):
        return msg.type
    elif isinstance(msg, dict) and 'role' in msg:
        return msg['role']
    elif hasattr(msg, '__class__'):
        return msg.__class__.__name__.lower().replace('message', '')
    else:
        return 'unknown'


def _has_tool_calls(msg):
    """Helper function to check if message has tool calls."""
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        return True
    elif isinstance(msg, dict) and msg.get('tool_calls'):
        return True
    else:
        return False


def _get_tool_calls(msg):
    """Helper function to extract tool calls from message."""
    if hasattr(msg, 'tool_calls'):
        return msg.tool_calls or []
    elif isinstance(msg, dict):
        return msg.get('tool_calls', [])
    else:
        return []


class TestUnderwritingEndToEnd:
    """Test suite for UnderwritingAgent end-to-end workflows."""
    
    def test_credit_analysis_workflow(self):
        """Test complete credit analysis workflow."""
        print("\n🔍 Testing credit analysis workflow...")
        
        try:
            agent = create_underwriting_agent()
            
            # Test credit analysis request
            messages = [{"role": "human", "content": "I need to analyze the credit risk for a borrower with a credit score of 680, applying for a conventional loan. They have no recent bankruptcies or foreclosures, but had 2 late payments (30-day) in the past year."}]
            
            result = agent.invoke({"messages": messages})
            
            # Validate response structure
            assert "messages" in result, "Result should contain messages"
            assert len(result["messages"]) > 1, "Should have multiple messages in conversation"
            
            # Check for tool usage
            tool_used = False
            for msg in result["messages"]:
                if _has_tool_calls(msg):
                    tool_calls = _get_tool_calls(msg)
                    for tool_call in tool_calls:
                        if isinstance(tool_call, dict) and tool_call.get('name') == 'analyze_credit_risk':
                            tool_used = True
                            break
                        elif hasattr(tool_call, 'name') and tool_call.name == 'analyze_credit_risk':
                            tool_used = True
                            break
            
            # Check final response content
            final_message = result["messages"][-1]
            final_content = _extract_message_content(final_message)
            
            if tool_used:
                assert "credit" in final_content.lower(), "Response should mention credit analysis"
                print(" Credit analysis workflow with tool usage completed")
            else:
                # Agent might provide direct response - verify it's relevant
                assert any(word in final_content.lower() for word in ["credit", "risk", "score", "underwriting"]), "Response should be relevant to credit analysis"
                print(" Credit analysis workflow completed (direct response)")
            
        except Exception as e:
            pytest.fail(f"Credit analysis workflow test failed: {e}")
    
    def test_dti_calculation_workflow(self):
        """Test complete DTI calculation workflow."""
        print("\n📊 Testing DTI calculation workflow...")
        
        try:
            agent = create_underwriting_agent()
            
            # Test DTI calculation request
            messages = [{"role": "human", "content": "Please calculate the debt-to-income ratio for a borrower with $8,000 monthly income, $2,200 proposed housing payment, and $800 in monthly debt payments for a conventional loan."}]
            
            result = agent.invoke({"messages": messages})
            
            # Validate response
            assert "messages" in result, "Result should contain messages"
            
            # Check final response content
            final_message = result["messages"][-1]
            final_content = _extract_message_content(final_message)
            
            # Should mention DTI concepts
            dti_keywords = ["dti", "debt", "income", "ratio", "front", "back"]
            assert any(keyword in final_content.lower() for keyword in dti_keywords), "Response should mention DTI concepts"
            
            print(" DTI calculation workflow completed")
            
        except Exception as e:
            pytest.fail(f"DTI calculation workflow test failed: {e}")
    
    def test_income_evaluation_workflow(self):
        """Test complete income evaluation workflow."""
        print("\n💰 Testing income evaluation workflow...")
        
        try:
            agent = create_underwriting_agent()
            
            # Test income evaluation request
            messages = [{"role": "human", "content": "I need to evaluate income sources for a borrower who has W2 salary of $6,000/month for 3 years, plus rental income of $1,200/month for 2 years. They're applying for a conventional loan."}]
            
            result = agent.invoke({"messages": messages})
            
            # Validate response
            assert "messages" in result, "Result should contain messages"
            
            # Check final response content
            final_message = result["messages"][-1]
            final_content = _extract_message_content(final_message)
            
            # Should mention income concepts
            income_keywords = ["income", "salary", "rental", "qualifying", "stable", "employment"]
            assert any(keyword in final_content.lower() for keyword in income_keywords), "Response should mention income concepts"
            
            print(" Income evaluation workflow completed")
            
        except Exception as e:
            pytest.fail(f"Income evaluation workflow test failed: {e}")
    
    def test_underwriting_decision_workflow(self):
        """Test complete underwriting decision workflow."""
        print("\n⚖️ Testing underwriting decision workflow...")
        
        try:
            agent = create_underwriting_agent()
            
            # Test comprehensive underwriting decision request
            messages = [{"role": "human", "content": "I need a complete underwriting decision for a borrower: credit score 720, monthly income $8,000, front-end DTI 25%, back-end DTI 38%, conventional loan for $400,000 with 20% down payment on a $500,000 property. Borrower has excellent income stability and 4 years employment."}]
            
            result = agent.invoke({"messages": messages})
            
            # Validate response
            assert "messages" in result, "Result should contain messages"
            
            # Check final response content
            final_message = result["messages"][-1]
            final_content = _extract_message_content(final_message)
            
            # Should provide underwriting guidance
            decision_keywords = ["underwriting", "decision", "approve", "analysis", "risk", "factors"]
            assert any(keyword in final_content.lower() for keyword in decision_keywords), "Response should mention underwriting decision concepts"
            
            print(" Underwriting decision workflow completed")
            
        except Exception as e:
            pytest.fail(f"Underwriting decision workflow test failed: {e}")
    
    def test_multi_step_analysis_workflow(self):
        """Test multi-step analysis workflow covering multiple underwriting aspects."""
        print("\n🔄 Testing multi-step analysis workflow...")
        
        try:
            agent = create_underwriting_agent()
            
            # Start with credit analysis
            messages = [{"role": "human", "content": "I need a comprehensive underwriting analysis. Let's start with credit risk for a borrower with credit score 705, no bankruptcies, 1 late payment last year."}]
            
            result = agent.invoke({"messages": messages})
            
            # Continue with DTI analysis
            conversation = result["messages"]
            conversation.append({"role": "human", "content": "Now calculate DTI with $7,500 monthly income, $2,000 housing payment, $900 other debts."})
            
            result = agent.invoke({"messages": conversation})
            
            # Validate multi-step conversation
            assert len(result["messages"]) >= 4, "Should have multiple conversation turns"
            
            # Check that agent maintained context
            final_message = result["messages"][-1]
            final_content = _extract_message_content(final_message)
            
            # Should show engagement with multi-step process (robust checking)
            analysis_keywords = ["analysis", "dti", "credit", "calculation", "underwriting"]
            context_keywords = ["income", "borrower", "debt", "ratio", "loan", "mortgage"]
            
            # Check for analysis keywords OR contextual keywords (more robust)
            has_analysis_terms = any(keyword in final_content.lower() for keyword in analysis_keywords)
            has_context_terms = any(keyword in final_content.lower() for keyword in context_keywords)
            
            assert has_analysis_terms or has_context_terms, f"Response should engage with analysis request. Content: {final_content[:200]}..."
            
            print(" Multi-step analysis workflow completed")
            
        except Exception as e:
            pytest.fail(f"Multi-step analysis workflow test failed: {e}")
    
    def test_error_recovery_workflow(self):
        """Test how agent handles and recovers from errors."""
        print("\n⚠️ Testing error recovery workflow...")
        
        try:
            agent = create_underwriting_agent()
            
            # Test with incomplete information
            messages = [{"role": "human", "content": "Analyze credit risk for a borrower."}]  # Vague request
            
            result = agent.invoke({"messages": messages})
            
            # Agent should ask for clarification or provide guidance
            final_message = result["messages"][-1]
            final_content = _extract_message_content(final_message)
            
            # Should request more information or provide helpful guidance
            helpful_keywords = ["information", "details", "credit score", "need", "provide", "help"]
            assert any(keyword in final_content.lower() for keyword in helpful_keywords), "Agent should request needed information"
            
            print(" Error recovery workflow completed")
            
        except Exception as e:
            pytest.fail(f"Error recovery workflow test failed: {e}")
    
    def test_professional_communication_workflow(self):
        """Test that agent maintains professional underwriting communication."""
        print("\n💼 Testing professional communication workflow...")
        
        try:
            agent = create_underwriting_agent()
            
            # Test professional interaction
            messages = [{"role": "human", "content": "What's your role as an underwriting agent?"}]
            
            result = agent.invoke({"messages": messages})
            
            # Check response professionalism
            final_message = result["messages"][-1]
            final_content = _extract_message_content(final_message)
            
            # Should mention underwriting role professionally
            professional_keywords = ["underwriting", "analysis", "risk", "decisions", "mortgage", "lending"]
            assert any(keyword in final_content.lower() for keyword in professional_keywords), "Response should be professional and relevant"
            
            # Should not be overly casual
            assert len(final_content) > 50, "Response should be substantive"
            
            print(" Professional communication workflow completed")
            
        except Exception as e:
            pytest.fail(f"Professional communication workflow test failed: {e}")


def run_end_to_end_tests():
    """Run all end-to-end tests and return results."""
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    test_class = TestUnderwritingEndToEnd()
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
    print("🧪 RUNNING UNDERWRITING AGENT END-TO-END TESTS")
    print("=" * 60)
    
    results = run_end_to_end_tests()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    
    print(f"\n📋 TEST DETAILS:")
    for detail in results["test_details"]:
        print(detail)
    
    if results["failed_tests"] == 0:
        print("\n🎉 ALL END-TO-END TESTS PASSED!")
    else:
        print(f"\n⚠️ {results['failed_tests']} TEST(S) FAILED")
        sys.exit(1)
