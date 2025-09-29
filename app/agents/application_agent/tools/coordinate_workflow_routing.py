"""
Workflow Routing Coordination Tool

This tool coordinates routing decisions across the agent workflow
based on Neo4j application intake rules.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from datetime import datetime

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection

logger = logging.getLogger(__name__)


def parse_neo4j_rule(rule_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON strings back to objects in Neo4j rule data."""
    parsed_rule = {}
    for key, value in rule_dict.items():
        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
            try:
                parsed_rule[key] = json.loads(value)
            except json.JSONDecodeError:
                parsed_rule[key] = value  # Keep as string if not valid JSON
        else:
            parsed_rule[key] = value
    return parsed_rule


class WorkflowRoutingRequest(BaseModel):
    """Workflow routing coordination request parameters."""
    application_id: str = Field(..., description="Application ID")
    current_status: str = Field(..., description="Current application status")
    application_complete: bool = Field(..., description="Application completeness status")
    qualification_status: str = Field(..., description="Initial qualification status (QUALIFIED, CONDITIONALLY_QUALIFIED, NOT_QUALIFIED)")
    credit_score: int = Field(..., description="Credit score")
    first_time_buyer: bool = Field(..., description="First-time home buyer status")
    loan_program_questions: bool = Field(default=False, description="Borrower has loan program questions")
    qualification_concerns: bool = Field(default=False, description="Qualification concerns identified")
    documents_verified: bool = Field(default=False, description="Documents verification status")
    appraisal_needed: bool = Field(default=True, description="Appraisal required")
    appraisal_completed: bool = Field(default=False, description="Appraisal completion status")
    property_value_questions: bool = Field(default=False, description="Property value questions")
    market_analysis_needed: bool = Field(default=False, description="Market analysis needed")
    loan_purpose: str = Field(..., description="Loan purpose")
    property_type: str = Field(..., description="Property type")
    loan_amount: float = Field(..., description="Loan amount")
    
    # Priority factors
    purchase_contract_expiring: bool = Field(default=False, description="Purchase contract expiring soon")
    rate_lock_expiring: bool = Field(default=False, description="Rate lock expiring")
    closing_within_30_days: bool = Field(default=False, description="Closing scheduled within 30 days")


@tool(args_schema=WorkflowRoutingRequest)
def coordinate_workflow_routing(
    application_id: str,
    current_status: str,
    application_complete: bool,
    qualification_status: str,
    credit_score: int,
    first_time_buyer: bool,
    loan_program_questions: bool = False,
    qualification_concerns: bool = False,
    documents_verified: bool = False,
    appraisal_needed: bool = True,
    appraisal_completed: bool = False,
    property_value_questions: bool = False,
    market_analysis_needed: bool = False,
    loan_purpose: str = "purchase",
    property_type: str = "single_family_detached",
    loan_amount: float = 0,
    purchase_contract_expiring: bool = False,
    rate_lock_expiring: bool = False,
    closing_within_30_days: bool = False
) -> str:
    """
    Coordinate workflow routing decisions using Neo4j application intake rules.
    
    This tool analyzes application status and determines optimal routing
    through the agent workflow based on current state and requirements.
    """
    
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get workflow routing rules
            routing_query = """
            MATCH (rule:ApplicationIntakeRule)
            WHERE rule.category = 'WorkflowRouting'
            RETURN rule
            """
            result = session.run(routing_query)
            routing_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
        
        # Generate routing analysis report
        routing_report = []
        routing_report.append("WORKFLOW ROUTING ANALYSIS")
        routing_report.append("=" * 50)
        
        # Current Application State
        routing_report.append(f"\n📋 CURRENT APPLICATION STATE:")
        routing_report.append(f"Application ID: {application_id}")
        routing_report.append(f"Current Status: {current_status}")
        routing_report.append(f"Qualification: {qualification_status}")
        routing_report.append(f"Application Complete: {'' if application_complete else ''}")
        routing_report.append(f"Documents Verified: {'' if documents_verified else ''}")
        routing_report.append(f"Appraisal Complete: {'' if appraisal_completed else ''}")
        
        # Priority Assessment
        routing_report.append(f"\n⏰ PRIORITY ASSESSMENT:")
        
        priority_factors = []
        priority_level = "LOW"
        
        if purchase_contract_expiring:
            priority_factors.append("Purchase contract expiring")
            priority_level = "HIGH"
        if rate_lock_expiring:
            priority_factors.append("Rate lock expiring")
            priority_level = "HIGH" 
        if closing_within_30_days:
            priority_factors.append("Closing within 30 days")
            priority_level = "HIGH"
        
        # Get priority rules
        priority_rule = next((rule for rule in routing_rules if rule.get('rule_type') == 'priority_assignment'), {})
        priority_levels = priority_rule.get('priority_levels', {})
        
        if priority_level == "HIGH":
            routing_report.append(f"🔴 Priority Level: HIGH")
            for factor in priority_factors:
                routing_report.append(f"   • {factor}")
        elif loan_purpose == "refinance":
            priority_level = "MEDIUM"
            routing_report.append(f"🟡 Priority Level: MEDIUM (Refinance)")
        else:
            routing_report.append(f"🟢 Priority Level: LOW (Standard processing)")
        
        # Processing timeframes
        timeframes = priority_rule.get('processing_timeframes', {})
        if priority_level.lower() in timeframes:
            expected_response = timeframes[priority_level.lower()]
            routing_report.append(f"Expected Response Time: {expected_response.replace('_', ' ')}")
        
        # Current Workflow Position Analysis
        routing_report.append(f"\n🔄 WORKFLOW POSITION ANALYSIS:")
        
        workflow_stage = "initial"
        if appraisal_completed and documents_verified:
            workflow_stage = "ready_for_underwriting"
        elif documents_verified and appraisal_needed:
            workflow_stage = "ready_for_appraisal"
        elif application_complete and qualification_status in ["QUALIFIED", "CONDITIONALLY_QUALIFIED"]:
            workflow_stage = "ready_for_documents"
        elif not application_complete:
            workflow_stage = "incomplete_application"
        elif qualification_status == "NOT_QUALIFIED":
            workflow_stage = "needs_guidance"
        
        routing_report.append(f"Workflow Stage: {workflow_stage.replace('_', ' ').title()}")
        
        # Get routing logic
        routing_rule = next((rule for rule in routing_rules if rule.get('rule_type') == 'agent_routing'), {})
        routing_logic = routing_rule.get('routing_logic', {})
        routing_triggers = routing_rule.get('routing_triggers', {})
        
        # Routing Decision Analysis
        routing_report.append(f"\n🎯 ROUTING DECISION ANALYSIS:")
        
        routing_factors = []
        recommended_agent = None
        routing_reason = ""
        
        # Check for incomplete application
        if not application_complete:
            recommended_agent = "ApplicationAgent"
            routing_reason = "Application incomplete - return to applicant"
            routing_factors.append("Application missing required information")
        
        # Check for guidance needs
        elif (first_time_buyer or loan_program_questions or qualification_concerns or 
              credit_score < 650 or qualification_status == "NOT_QUALIFIED"):
            recommended_agent = "MortgageAdvisorAgent"
            routing_reason = "Guidance and education needed"
            if first_time_buyer:
                routing_factors.append("First-time home buyer needs guidance")
            if loan_program_questions:
                routing_factors.append("Loan program questions identified")
            if qualification_concerns:
                routing_factors.append("Qualification concerns need addressing")
            if credit_score < 650:
                routing_factors.append("Credit score below 650 - guidance beneficial")
            if qualification_status == "NOT_QUALIFIED":
                routing_factors.append("Initial qualification failed - improvement strategies needed")
        
        # Check for appraisal needs
        elif property_value_questions or market_analysis_needed:
            recommended_agent = "AppraisalAgent"
            routing_reason = "Property valuation analysis needed"
            if property_value_questions:
                routing_factors.append("Property value questions")
            if market_analysis_needed:
                routing_factors.append("Market analysis requested")
        
        # Check for standard workflow progression
        elif workflow_stage == "ready_for_documents":
            recommended_agent = "DocumentAgent"
            routing_reason = "Ready for document verification"
            routing_factors.append("Application complete and qualified")
            routing_factors.append("Standard document verification workflow")
        
        elif workflow_stage == "ready_for_appraisal" and appraisal_needed:
            recommended_agent = "AppraisalAgent"
            routing_reason = "Ready for property appraisal"
            routing_factors.append("Documents verified")
            routing_factors.append("Property appraisal required")
        
        elif workflow_stage == "ready_for_underwriting":
            recommended_agent = "UnderwritingAgent"
            routing_reason = "Ready for final underwriting decision"
            routing_factors.append("Documents verified")
            routing_factors.append("Appraisal completed")
            routing_factors.append("Ready for lending decision")
        
        else:
            recommended_agent = "MortgageAdvisorAgent"
            routing_reason = "Default routing for guidance"
            routing_factors.append("Standard guidance and consultation")
        
        # Display routing decision
        routing_report.append(f"Recommended Agent: {recommended_agent}")
        routing_report.append(f"Routing Reason: {routing_reason}")
        
        # Routing Factors
        routing_report.append(f"\n📊 ROUTING FACTORS:")
        for factor in routing_factors:
            routing_report.append(f"  • {factor}")
        
        # Workflow Sequence Planning
        routing_report.append(f"\n🗺️ COMPLETE WORKFLOW SEQUENCE:")
        
        workflow_sequence = []
        
        # Determine full workflow based on current state
        if not application_complete:
            workflow_sequence = [
                "1. ApplicationAgent - Complete application",
                "2. MortgageAdvisorAgent - Guidance (if needed)", 
                "3. DocumentAgent - Document verification",
                "4. AppraisalAgent - Property valuation",
                "5. UnderwritingAgent - Final approval"
            ]
        elif qualification_status == "NOT_QUALIFIED":
            workflow_sequence = [
                "1. MortgageAdvisorAgent - Improvement strategies",
                "2. ApplicationAgent - Re-qualification",
                "3. DocumentAgent - Document verification",
                "4. AppraisalAgent - Property valuation", 
                "5. UnderwritingAgent - Final approval"
            ]
        elif recommended_agent == "MortgageAdvisorAgent":
            workflow_sequence = [
                "1. MortgageAdvisorAgent - Guidance and education ← CURRENT",
                "2. DocumentAgent - Document verification",
                "3. AppraisalAgent - Property valuation",
                "4. UnderwritingAgent - Final approval"
            ]
        elif recommended_agent == "DocumentAgent":
            workflow_sequence = [
                "1. DocumentAgent - Document verification ← CURRENT",
                "2. AppraisalAgent - Property valuation",
                "3. UnderwritingAgent - Final approval"
            ]
        elif recommended_agent == "AppraisalAgent":
            workflow_sequence = [
                "1. AppraisalAgent - Property valuation ← CURRENT",
                "2. UnderwritingAgent - Final approval"
            ]
        elif recommended_agent == "UnderwritingAgent":
            workflow_sequence = [
                "1. UnderwritingAgent - Final approval ← CURRENT"
            ]
        
        for step in workflow_sequence:
            routing_report.append(f"  {step}")
        
        # Special Handling Requirements
        routing_report.append(f"\n⚠️ SPECIAL HANDLING REQUIREMENTS:")
        
        special_requirements = []
        
        if priority_level == "HIGH":
            special_requirements.append("Expedited processing required")
            special_requirements.append("Daily status updates needed")
        
        if qualification_status == "CONDITIONALLY_QUALIFIED":
            special_requirements.append("Manual underwriting may be required")
            special_requirements.append("Additional documentation likely needed")
        
        if property_type in ["condominium", "manufactured", "multi_family_2_4_units"]:
            special_requirements.append("Specialized property type - additional requirements")
        
        if loan_amount > 1000000:
            special_requirements.append("Jumbo loan - enhanced documentation required")
        
        if not special_requirements:
            special_requirements.append("Standard processing requirements")
        
        for req in special_requirements:
            routing_report.append(f"  • {req}")
        
        # Communication Requirements
        routing_report.append(f"\n📞 COMMUNICATION REQUIREMENTS:")
        
        # Get communication rules
        comm_rule = next((rule for rule in routing_rules if rule.get('rule_type') == 'communication_requirements'), {})
        notification_triggers = comm_rule.get('notification_triggers', {})
        
        if priority_level == "HIGH":
            routing_report.append("• Immediate notification to applicant required")
            routing_report.append("• Daily progress updates")
            routing_report.append("• Senior management notification")
        else:
            routing_report.append("• Standard status update notifications")
            routing_report.append("• Weekly progress reports")
        
        # Next Steps and Timeline
        routing_report.append(f"\n📅 NEXT STEPS AND TIMELINE:")
        
        if priority_level == "HIGH":
            routing_report.append("⏰ IMMEDIATE ACTION REQUIRED:")
            routing_report.append("1. Route to recommended agent within 1 hour")
            routing_report.append("2. Set up expedited processing")
            routing_report.append("3. Notify all stakeholders immediately")
        else:
            routing_report.append("📋 STANDARD PROCESSING:")
            routing_report.append("1. Route to recommended agent within 24 hours")
            routing_report.append("2. Follow standard processing timelines")
            routing_report.append("3. Provide regular status updates")
        
        # Success Metrics
        routing_report.append(f"\n📈 SUCCESS METRICS:")
        routing_report.append(f"• Target Processing Time: {expected_response if 'expected_response' in locals() else 'Standard timeline'}")
        routing_report.append(f"• Quality Checkpoints: Agent handoffs verified")
        routing_report.append(f"• Customer Communication: Regular updates provided")
        routing_report.append(f"• Escalation Triggers: Monitored for delays")
        
        # Final Routing Instruction
        routing_report.append(f"\n ROUTING INSTRUCTION:")
        routing_report.append(f"ROUTE APPLICATION {application_id} TO: {recommended_agent}")
        routing_report.append(f"PRIORITY: {priority_level}")
        routing_report.append(f"REASON: {routing_reason}")
        routing_report.append(f"TIMELINE: {expected_response if 'expected_response' in locals() else 'Standard processing'}")
        
        return "\n".join(routing_report)
        
    except Exception as e:
        logger.error(f"Error during workflow routing: {e}")
        return f" Error during workflow routing: {str(e)}"


def validate_tool() -> bool:
    """Validate that the coordinate_workflow_routing tool works correctly."""
    try:
        # Test with sample data
        result = coordinate_workflow_routing.invoke({
            "application_id": "APP_20240101_123456_SMI",
            "current_status": "received",
            "application_complete": True,
            "qualification_status": "QUALIFIED",
            "credit_score": 720,
            "first_time_buyer": False,
            "loan_program_questions": False,
            "qualification_concerns": False,
            "documents_verified": False,
            "appraisal_needed": True,
            "appraisal_completed": False,
            "property_value_questions": False,
            "market_analysis_needed": False,
            "loan_purpose": "purchase",
            "property_type": "single_family_detached",
            "loan_amount": 400000.0,
            "purchase_contract_expiring": False,
            "rate_lock_expiring": False,
            "closing_within_30_days": False
        })
        return "WORKFLOW ROUTING ANALYSIS" in result and "ROUTING INSTRUCTION" in result
    except Exception as e:
        print(f"Workflow routing tool validation failed: {e}")
        return False
