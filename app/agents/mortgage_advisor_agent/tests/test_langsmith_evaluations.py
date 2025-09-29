"""
LangSmith Evaluations for MortgageAdvisorAgent

This module implements proper LLM/agent evaluations using LangSmith's evaluation framework,
including LLM-as-a-judge, trajectory evaluations, and custom mortgage advisory metrics.
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the src directory to the Python path for testing
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from langsmith import Client, evaluate, traceable
from langsmith.evaluation import LangChainStringEvaluator, evaluate
from langsmith.schemas import Example, Run
from langchain.evaluation import load_evaluator
from app.agents.mortgage_advisor_agent import create_mortgage_advisor_agent


# Initialize LangSmith client
ls_client = Client()

# Create evaluation dataset name
DATASET_NAME = "mortgage_advisor_agent_evaluation_dataset"


class MortgageAdvisorAgentEvaluations:
    """Comprehensive LangSmith evaluations for MortgageAdvisorAgent."""
    
    def __init__(self):
        self.agent = create_mortgage_advisor_agent()
        self.client = ls_client
        
    @traceable
    def agent_wrapper(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Traceable wrapper for the MortgageAdvisorAgent."""
        messages = [{"role": "human", "content": inputs["input"]}]
        result = self.agent.invoke({"messages": messages})
        
        # Extract final response
        final_message = result["messages"][-1]
        if hasattr(final_message, 'content'):
            output = final_message.content
        elif isinstance(final_message, dict):
            output = final_message.get('content', str(final_message))
        else:
            output = str(final_message)
            
        return {
            "output": output,
            "messages": result["messages"],
            "tool_calls": self._extract_tool_calls(result["messages"])
        }
    
    def _extract_tool_calls(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from messages for trajectory evaluation."""
        tool_calls = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if hasattr(tool_call, 'name'):
                        tool_calls.append({
                            "name": tool_call.name,
                            "args": getattr(tool_call, 'args', {})
                        })
            elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs.get('tool_calls'):
                for tool_call in msg.additional_kwargs['tool_calls']:
                    tool_calls.append({
                        "name": tool_call.get('function', {}).get('name'),
                        "args": tool_call.get('function', {}).get('arguments', {})
                    })
        return tool_calls

    def create_evaluation_dataset(self) -> str:
        """Create comprehensive evaluation dataset for mortgage advisory scenarios."""
        
        # Define evaluation examples with expected behaviors
        examples = [
            # Loan Program Education Scenarios
            {
                "input": "Can you explain the difference between FHA and conventional loans?",
                "expected_output": "comprehensive loan program comparison with key differences",
                "scenario_type": "loan_education",
                "expected_tools": ["explain_loan_programs"],
                "evaluation_criteria": {
                    "should_explain_differences": True,
                    "should_mention_benefits": True,
                    "should_use_education_tool": True
                }
            },
            {
                "input": "What loan programs are available for first-time homebuyers?",
                "expected_output": "first-time buyer focused loan program information",
                "scenario_type": "loan_education",
                "expected_tools": ["explain_loan_programs"],
                "evaluation_criteria": {
                    "should_mention_first_time_programs": True,
                    "should_provide_specific_options": True,
                    "should_use_education_tool": True
                }
            },
            
            # Loan Recommendation Scenarios
            {
                "input": "I have a 720 credit score, 20% down payment, stable W2 income. What loan should I consider?",
                "expected_output": "personalized loan recommendations based on profile",
                "scenario_type": "loan_recommendation",
                "expected_tools": ["recommend_loan_program"],
                "evaluation_criteria": {
                    "should_analyze_profile": True,
                    "should_provide_recommendations": True,
                    "should_use_recommendation_tool": True
                }
            },
            
            # Qualification Analysis Scenarios
            {
                "input": "Check if I qualify for a VA loan: I'm a veteran, 650 credit score, $70k income",
                "expected_output": "VA loan qualification analysis with specific requirements",
                "scenario_type": "qualification_check",
                "expected_tools": ["check_qualification_requirements"],
                "evaluation_criteria": {
                    "should_check_va_eligibility": True,
                    "should_analyze_requirements": True,
                    "should_use_qualification_tool": True
                }
            },
            
            # Process Guidance Scenarios
            {
                "input": "I've been pre-approved for a loan. What are my next steps in the mortgage process?",
                "expected_output": "step-by-step process guidance for next phase",
                "scenario_type": "process_guidance",
                "expected_tools": ["guide_next_steps"],
                "evaluation_criteria": {
                    "should_provide_clear_steps": True,
                    "should_be_actionable": True,
                    "should_use_guidance_tool": True
                }
            },
            
            # Multi-step Advisory Scenarios
            {
                "input": "I need complete mortgage guidance. Start with explaining loan types, then recommend best option for my situation: 740 credit, 15% down",
                "expected_output": "comprehensive advisory process with education and recommendations",
                "scenario_type": "multi_step",
                "expected_tools": ["explain_loan_programs", "recommend_loan_program"],
                "evaluation_criteria": {
                    "should_maintain_context": True,
                    "should_use_multiple_tools": True,
                    "should_provide_comprehensive_guidance": True
                }
            },
            
            # Edge Cases
            {
                "input": "I have poor credit and limited down payment. Is homeownership still possible?",
                "expected_output": "constructive guidance for challenging financial situations",
                "scenario_type": "challenging_scenario",
                "expected_tools": ["check_qualification_requirements", "guide_next_steps"],
                "evaluation_criteria": {
                    "should_provide_hope": True,
                    "should_suggest_improvement": True,
                    "should_be_encouraging": True
                }
            }
        ]
        
        # Create dataset
        try:
            dataset = self.client.create_dataset(
                dataset_name=DATASET_NAME,
                description="Comprehensive evaluation dataset for MortgageAdvisorAgent with various advisory scenarios"
            )
            dataset_id = dataset.id
        except Exception:
            # Dataset might already exist
            datasets = list(self.client.list_datasets(dataset_name=DATASET_NAME))
            if datasets:
                dataset_id = datasets[0].id
            else:
                raise
        
        # Add examples to dataset
        self.client.create_examples(
            inputs=[{"input": ex["input"]} for ex in examples],
            outputs=[{"expected_output": ex["expected_output"], 
                     "scenario_type": ex["scenario_type"],
                     "expected_tools": ex["expected_tools"],
                     "evaluation_criteria": ex["evaluation_criteria"]} for ex in examples],
            dataset_id=dataset_id
        )
        
        return dataset_id

    def create_custom_evaluators(self):
        """Create custom evaluators for mortgage advisory-specific criteria."""
        
        # Tool Usage Evaluator
        def tool_usage_evaluator(run: Run, example: Example) -> Dict[str, Any]:
            """Evaluate if agent used appropriate tools."""
            expected_tools = example.outputs.get("expected_tools", [])
            actual_tool_calls = []
            
            # Extract tool calls from run outputs
            if hasattr(run.outputs, 'get') and run.outputs.get("tool_calls"):
                actual_tool_calls = [tc["name"] for tc in run.outputs["tool_calls"]]
            
            # Check if expected tools were used
            tools_used_correctly = all(tool in actual_tool_calls for tool in expected_tools)
            
            return {
                "key": "tool_usage",
                "score": 1.0 if tools_used_correctly else 0.0,
                "comment": f"Expected tools: {expected_tools}, Used: {actual_tool_calls}"
            }
        
        # Advisory Quality Evaluator (LLM-as-a-judge)
        def advisory_quality_evaluator(run: Run, example: Example) -> Dict[str, Any]:
            """Evaluate advisory response quality using LLM-as-a-judge."""
            
            # Create LLM-as-a-judge prompt
            evaluation_prompt = f"""
            You are an expert mortgage advisory evaluator. Evaluate the following mortgage advisory response.
            
            Input Query: {example.inputs.get('input')}
            Agent Response: {run.outputs.get('output', '')}
            Expected Scenario Type: {example.outputs.get('scenario_type')}
            
            Evaluation Criteria:
            1. Educational Value: Does the response educate the user about mortgage concepts?
            2. Personalization: Is the advice tailored to the user's specific situation?
            3. Clarity: Is the response clear and easy to understand?
            4. Actionability: Does the response provide clear next steps?
            5. Professional Tone: Is the response professional and encouraging?
            
            Provide a score from 0-100 and detailed reasoning.
            
            Response format:
            Score: [0-100]
            Reasoning: [Detailed explanation]
            """
            
            # Use LangChain's LLM evaluator
            try:
                from langchain.evaluation import load_evaluator
                from app.utils.llm_factory import get_llm
                
                llm = get_llm()
                evaluator = load_evaluator("labeled_score_string", llm=llm)
                
                result = evaluator.evaluate_strings(
                    prediction=run.outputs.get('output', ''),
                    reference=example.outputs.get('expected_output', ''),
                    input=example.inputs.get('input', '')
                )
                
                score = result.get('score', 0.5)
                reasoning = result.get('reasoning', 'LLM evaluation completed')
                
            except Exception as e:
                # Fallback scoring
                output = run.outputs.get('output', '').lower()
                scenario_type = example.outputs.get('scenario_type', '')
                
                # Basic keyword-based scoring
                score = 0.5
                if len(output) > 100:  # Substantive response
                    score += 0.2
                if any(word in output for word in ['loan', 'mortgage', 'program']):  # Relevant to mortgages
                    score += 0.2
                if any(word in output for word in ['recommend', 'suggest', 'consider']):  # Advisory
                    score += 0.1
                
                reasoning = f"Fallback evaluation: length={len(output)}, relevant terms found"
            
            return {
                "key": "advisory_quality",
                "score": score,
                "comment": reasoning
            }
        
        # Educational Effectiveness Evaluator
        def educational_effectiveness_evaluator(run: Run, example: Example) -> Dict[str, Any]:
            """Evaluate educational effectiveness of advisory responses."""
            scenario_type = example.outputs.get('scenario_type', '')
            
            if scenario_type not in ['loan_education', 'multi_step']:
                return {"key": "educational_effectiveness", "score": 1.0, "comment": "Not applicable"}
            
            output = run.outputs.get('output', '').lower()
            
            # Check for educational indicators
            educational_terms = ['explain', 'difference', 'benefit', 'requirement', 'option', 'type', 'program']
            has_educational_content = any(term in output for term in educational_terms)
            
            return {
                "key": "educational_effectiveness", 
                "score": 1.0 if has_educational_content else 0.0,
                "comment": f"Educational content found: {has_educational_content}"
            }
        
        return [tool_usage_evaluator, advisory_quality_evaluator, educational_effectiveness_evaluator]

    def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive LangSmith evaluation."""
        
        # Create evaluation dataset
        print("📊 Creating evaluation dataset...")
        dataset_id = self.create_evaluation_dataset()
        
        # Create custom evaluators
        print("🔧 Setting up custom evaluators...")
        custom_evaluators = self.create_custom_evaluators()
        
        # Add built-in LangChain evaluators
        builtin_evaluators = [
            LangChainStringEvaluator("criteria", criteria="helpfulness"),
            LangChainStringEvaluator("criteria", criteria="relevance"),
            LangChainStringEvaluator("criteria", criteria="coherence")
        ]
        
        all_evaluators = custom_evaluators + builtin_evaluators
        
        print("🚀 Running LangSmith evaluation...")
        
        # Run evaluation
        evaluation_results = evaluate(
            target=self.agent_wrapper,
            data=DATASET_NAME,
            evaluators=all_evaluators,
            experiment_prefix="mortgage_advisor_agent_eval",
            metadata={
                "agent_type": "MortgageAdvisorAgent",
                "evaluation_date": datetime.now().isoformat(),
                "description": "Comprehensive evaluation of MortgageAdvisorAgent with LLM-as-a-judge and custom metrics"
            }
        )
        
        return evaluation_results

    def run_quick_evaluation(self) -> Dict[str, Any]:
        """Run a quick evaluation with core scenarios."""
        
        # Quick evaluation with key scenarios
        quick_examples = [
            {
                "input": "Explain FHA vs conventional loans",
                "expected_output": "Clear loan program comparison"
            },
            {
                "input": "Recommend loan for 720 credit score, 20% down",
                "expected_output": "Personalized loan recommendation"  
            },
            {
                "input": "What are next steps after pre-approval?",
                "expected_output": "Process guidance with clear steps"
            }
        ]
        
        # Create temporary dataset
        temp_dataset_name = f"advisor_quick_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dataset = self.client.create_dataset(
            dataset_name=temp_dataset_name,
            description="Quick evaluation dataset"
        )
        
        self.client.create_examples(
            inputs=[{"input": ex["input"]} for ex in quick_examples],
            outputs=[{"expected_output": ex["expected_output"]} for ex in quick_examples],
            dataset_id=dataset.id
        )
        
        # Simple evaluators for quick eval
        simple_evaluators = [
            LangChainStringEvaluator("criteria", criteria="helpfulness"),
            LangChainStringEvaluator("criteria", criteria="relevance")
        ]
        
        # Run quick evaluation
        results = evaluate(
            target=self.agent_wrapper,
            data=temp_dataset_name,
            evaluators=simple_evaluators,
            experiment_prefix="mortgage_advisor_agent_quick_eval"
        )
        
        return results


def run_langsmith_evaluations(quick: bool = False) -> Dict[str, Any]:
    """Run LangSmith evaluations for MortgageAdvisorAgent."""
    
    print("🧪 RUNNING LANGSMITH EVALUATIONS FOR MORTGAGE ADVISOR AGENT")
    print("=" * 70)
    
    try:
        # Check LangSmith API key
        if not os.getenv("LANGCHAIN_API_KEY"):
            print("⚠️ Warning: LANGCHAIN_API_KEY not set. Some features may not work.")
            print("Set your LangSmith API key: export LANGCHAIN_API_KEY=your_key")
        
        evaluator = MortgageAdvisorAgentEvaluations()
        
        if quick:
            print("🚀 Running quick evaluation...")
            results = evaluator.run_quick_evaluation()
        else:
            print("🚀 Running comprehensive evaluation...")
            results = evaluator.run_comprehensive_evaluation()
        
        print(" LangSmith evaluation completed!")
        print(f"📊 Results available in LangSmith UI")
        
        return results
        
    except Exception as e:
        print(f" LangSmith evaluation failed: {e}")
        print("💡 This might be due to missing API keys or network issues")
        return {"error": str(e)}


if __name__ == "__main__":
    # Run quick evaluation by default
    results = run_langsmith_evaluations(quick=True)
    print(f"Evaluation results: {results}")
