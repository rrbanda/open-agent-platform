"""
LangSmith Evaluations for UnderwritingAgent

This module implements proper LLM/agent evaluations using LangSmith's evaluation framework,
including LLM-as-a-judge, trajectory evaluations, and custom underwriting metrics.
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
from app.agents.underwriting_agent import create_underwriting_agent


# Initialize LangSmith client
ls_client = Client()

# Create evaluation dataset name
DATASET_NAME = "underwriting_agent_evaluation_dataset"


class UnderwritingAgentEvaluations:
    """Comprehensive LangSmith evaluations for UnderwritingAgent."""
    
    def __init__(self):
        self.agent = create_underwriting_agent()
        self.client = ls_client
        
    @traceable
    def agent_wrapper(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Traceable wrapper for the UnderwritingAgent."""
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
        """Create comprehensive evaluation dataset for underwriting scenarios."""
        
        # Define evaluation examples with expected behaviors
        examples = [
            # Credit Analysis Scenarios
            {
                "input": "Analyze credit risk for a borrower with credit score 780, no derogatory events, 7 years credit history, conventional loan",
                "expected_output": "low risk assessment with positive indicators",
                "scenario_type": "credit_analysis",
                "expected_tools": ["analyze_credit_risk"],
                "evaluation_criteria": {
                    "should_identify_low_risk": True,
                    "should_mention_excellent_credit": True,
                    "should_use_credit_tool": True
                }
            },
            {
                "input": "Credit analysis for borrower: 580 credit score, bankruptcy 12 months ago, multiple late payments",
                "expected_output": "high risk assessment with concerns identified",
                "scenario_type": "credit_analysis", 
                "expected_tools": ["analyze_credit_risk"],
                "evaluation_criteria": {
                    "should_identify_high_risk": True,
                    "should_mention_concerns": True,
                    "should_use_credit_tool": True
                }
            },
            
            # DTI Analysis Scenarios
            {
                "input": "Calculate DTI for borrower: $8,000 monthly income, $2,200 housing payment, $800 other debts, conventional loan",
                "expected_output": "DTI calculations with program compliance assessment",
                "scenario_type": "dti_analysis",
                "expected_tools": ["calculate_debt_to_income"],
                "evaluation_criteria": {
                    "should_calculate_dti": True,
                    "should_assess_compliance": True,
                    "should_use_dti_tool": True
                }
            },
            
            # Income Evaluation Scenarios  
            {
                "input": "Evaluate income sources: W2 salary $6,000/month for 3 years, bonus $500/month for 2 years, conventional loan",
                "expected_output": "income qualification analysis with usability assessment",
                "scenario_type": "income_evaluation",
                "expected_tools": ["evaluate_income_sources"],
                "evaluation_criteria": {
                    "should_evaluate_income": True,
                    "should_assess_stability": True,
                    "should_use_income_tool": True
                }
            },
            
            # Comprehensive Underwriting Scenarios
            {
                "input": "Make underwriting decision: credit 720, income $8,000, front DTI 25%, back DTI 35%, conventional loan, 20% down, excellent employment",
                "expected_output": "comprehensive underwriting decision with reasoning",
                "scenario_type": "underwriting_decision",
                "expected_tools": ["make_underwriting_decision"],
                "evaluation_criteria": {
                    "should_make_decision": True,
                    "should_provide_reasoning": True,
                    "should_use_decision_tool": True
                }
            },
            
            # Multi-step Analysis Scenarios
            {
                "input": "I need complete underwriting analysis. Start with credit score 695, then calculate DTI with $7,500 income, $2,000 housing, $900 debts",
                "expected_output": "multi-step analysis with context maintenance",
                "scenario_type": "multi_step",
                "expected_tools": ["analyze_credit_risk", "calculate_debt_to_income"],
                "evaluation_criteria": {
                    "should_maintain_context": True,
                    "should_use_multiple_tools": True,
                    "should_provide_comprehensive_analysis": True
                }
            },
            
            # Edge Cases
            {
                "input": "What should I do if borrower has insufficient income documentation?",
                "expected_output": "professional guidance on documentation requirements",
                "scenario_type": "guidance",
                "expected_tools": [],
                "evaluation_criteria": {
                    "should_provide_guidance": True,
                    "should_be_professional": True,
                    "should_mention_documentation": True
                }
            }
        ]
        
        # Create dataset
        try:
            dataset = self.client.create_dataset(
                dataset_name=DATASET_NAME,
                description="Comprehensive evaluation dataset for UnderwritingAgent with various underwriting scenarios"
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
        """Create custom evaluators for underwriting-specific criteria."""
        
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
        
        # Underwriting Quality Evaluator (LLM-as-a-judge)
        def underwriting_quality_evaluator(run: Run, example: Example) -> Dict[str, Any]:
            """Evaluate underwriting response quality using LLM-as-a-judge."""
            
            # Create LLM-as-a-judge prompt
            evaluation_prompt = f"""
            You are an expert mortgage underwriting evaluator. Evaluate the following underwriting analysis response.
            
            Input Query: {example.inputs.get('input')}
            Agent Response: {run.outputs.get('output', '')}
            Expected Scenario Type: {example.outputs.get('scenario_type')}
            
            Evaluation Criteria:
            1. Technical Accuracy: Is the underwriting analysis technically correct?
            2. Completeness: Does the response address all aspects of the query?
            3. Professional Tone: Is the response professional and appropriate?
            4. Actionable Guidance: Does the response provide clear next steps?
            5. Risk Assessment: If applicable, is the risk assessment appropriate?
            
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
                if scenario_type in output:  # Relevant to scenario
                    score += 0.2
                if any(word in output for word in ['recommend', 'suggest', 'consider']):  # Actionable
                    score += 0.1
                
                reasoning = f"Fallback evaluation: length={len(output)}, relevant terms found"
            
            return {
                "key": "underwriting_quality",
                "score": score,
                "comment": reasoning
            }
        
        # Context Maintenance Evaluator
        def context_maintenance_evaluator(run: Run, example: Example) -> Dict[str, Any]:
            """Evaluate if agent maintains context in multi-step scenarios."""
            scenario_type = example.outputs.get('scenario_type', '')
            
            if scenario_type != 'multi_step':
                return {"key": "context_maintenance", "score": 1.0, "comment": "Not applicable"}
            
            output = run.outputs.get('output', '').lower()
            
            # Check for context indicators
            context_indicators = ['previous', 'earlier', 'now', 'next', 'continue', 'also', 'additionally']
            has_context = any(indicator in output for indicator in context_indicators)
            
            return {
                "key": "context_maintenance", 
                "score": 1.0 if has_context else 0.0,
                "comment": f"Context indicators found: {has_context}"
            }
        
        return [tool_usage_evaluator, underwriting_quality_evaluator, context_maintenance_evaluator]

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
            experiment_prefix="underwriting_agent_eval",
            metadata={
                "agent_type": "UnderwritingAgent",
                "evaluation_date": datetime.now().isoformat(),
                "description": "Comprehensive evaluation of UnderwritingAgent with LLM-as-a-judge and custom metrics"
            }
        )
        
        return evaluation_results

    def run_quick_evaluation(self) -> Dict[str, Any]:
        """Run a quick evaluation with core scenarios."""
        
        # Quick evaluation with key scenarios
        quick_examples = [
            {
                "input": "Analyze credit risk for borrower with 750 credit score, no derogatory events",
                "expected_output": "Low risk assessment with positive recommendations"
            },
            {
                "input": "Calculate DTI: $8,000 income, $2,000 housing, $800 debts",
                "expected_output": "DTI calculation with compliance assessment"  
            },
            {
                "input": "Make underwriting decision: good credit, acceptable DTI, stable income",
                "expected_output": "Approval recommendation with reasoning"
            }
        ]
        
        # Create temporary dataset
        temp_dataset_name = f"quick_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
            experiment_prefix="underwriting_agent_quick_eval"
        )
        
        return results


def run_langsmith_evaluations(quick: bool = False) -> Dict[str, Any]:
    """Run LangSmith evaluations for UnderwritingAgent."""
    
    print("🧪 RUNNING LANGSMITH EVALUATIONS FOR UNDERWRITING AGENT")
    print("=" * 70)
    
    try:
        # Check LangSmith API key
        if not os.getenv("LANGCHAIN_API_KEY"):
            print("⚠️ Warning: LANGCHAIN_API_KEY not set. Some features may not work.")
            print("Set your LangSmith API key: export LANGCHAIN_API_KEY=your_key")
        
        evaluator = UnderwritingAgentEvaluations()
        
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
