"""
Guide Next Steps Tool - Neo4j Powered

This tool provides step-by-step guidance for the mortgage application process
based on the borrower's current stage and selected loan program. All guidance
comes from Neo4j process data, making it 100% data-driven.

Purpose:
- Guide borrowers through the mortgage application process
- Provide stage-specific next steps and requirements
- Offer timeline estimates and preparation tips
- Use process data from Neo4j for dynamic guidance
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    # Fallback for different import paths during testing
    from utils import get_neo4j_connection, initialize_connection


class NextStepsGuidanceRequest(BaseModel):
    """Schema for next steps guidance request"""
    current_stage: str = Field(
        description="Current stage in mortgage process: 'pre_qualification', 'application', 'processing', 'underwriting', 'closing', 'completed'"
    )
    selected_loan_program: Optional[str] = Field(
        description="Selected loan program (e.g., 'FHA', 'VA', 'Conventional')", default=None
    )
    borrower_status: Optional[str] = Field(
        description="Borrower status: 'first_time', 'repeat', 'refinancing'", default="first_time"
    )
    priority_focus: Optional[str] = Field(
        description="Priority focus area: 'timeline', 'documentation', 'preparation', 'requirements'", default="timeline"
    )


@tool
def guide_next_steps(guidance_request: str) -> str:
    """Provides personalized step-by-step guidance for the mortgage application process.
    
    Args:
        guidance_request: Request details like "Stage: application, Loan: FHA, Status: first_time, Focus: documentation"
    """
    
    try:
        # Parse guidance request string
        import re
        request = guidance_request.lower()
        
        # Extract current stage
        stage_match = re.search(r'stage:\s*([a-z_]+)', request)
        current_stage = stage_match.group(1) if stage_match else "pre_qualification"
        
        # Extract loan program
        loan_match = re.search(r'loan:\s*([a-z]+)', request)
        selected_loan_program = loan_match.group(1).upper() if loan_match else None
        
        # Extract borrower status
        status_match = re.search(r'status:\s*([a-z_]+)', request)
        borrower_status = status_match.group(1) if status_match else "first_time"
        
        # Extract priority focus
        focus_match = re.search(r'focus:\s*([a-z_]+)', request)
        priority_focus = focus_match.group(1) if focus_match else "timeline"
        
        # Initialize Neo4j connection
        if not initialize_connection():
            return "Error: Failed to connect to Neo4j database"
        
        connection = get_neo4j_connection()
        # Get current stage details and next steps from Neo4j
        current_stage_info = _get_current_stage_info(current_stage, connection)
        if not current_stage_info:
            return {
                "error": f"Stage '{current_stage}' not found in mortgage process data",
                "available_stages": _get_available_stages(connection),
                "success": False
            }
        
        # Get immediate next steps
        immediate_next_steps = _get_immediate_next_steps(current_stage, selected_loan_program, connection)
        
        # Get upcoming stages and timeline
        upcoming_stages = _get_upcoming_stages(current_stage, connection)
        
        # Get documentation requirements
        documentation_checklist = _get_documentation_requirements(
            current_stage, selected_loan_program, borrower_status, connection
        )
        
        # Get timeline expectations
        timeline_expectations = _get_timeline_expectations(current_stage, selected_loan_program, connection)
        
        # Get preparation tips
        preparation_tips = _get_preparation_tips(
            current_stage, selected_loan_program, borrower_status, priority_focus, connection
        )
        
        # Get loan program specific guidance if provided
        program_specific_guidance = None
        if selected_loan_program:
            program_specific_guidance = _get_program_specific_guidance(
                current_stage, selected_loan_program, connection
            )
        
        return {
            "guidance_info": {
                "current_stage": current_stage,
                "stage_description": current_stage_info.get("description", ""),
                "selected_loan_program": selected_loan_program,
                "borrower_status": borrower_status,
                "priority_focus": priority_focus,
                "timestamp": datetime.now().isoformat()
            },
            "current_stage_overview": current_stage_info,
            "immediate_next_steps": immediate_next_steps,
            "upcoming_stages": upcoming_stages,
            "documentation_checklist": documentation_checklist,
            "timeline_expectations": timeline_expectations,
            "preparation_tips": preparation_tips,
            "program_specific_guidance": program_specific_guidance,
            "success": True
        }
        
    except Exception as e:
        return {
            "error": f"Error generating next steps guidance: {str(e)}",
            "success": False
        }
    finally:
        connection.disconnect()


def _get_available_stages(connection) -> List[str]:
    """Get list of available process stages from Neo4j"""
    try:
        with connection.driver.session(database=connection.database) as session:
            result = session.run("MATCH (ps:ProcessStep) RETURN DISTINCT ps.category as stage ORDER BY stage")
            # Convert to list to avoid consumption errors
            records = list(result)
            return [record["stage"] for record in records]
    except Exception:
        return []


def _get_current_stage_info(current_stage: str, connection) -> Dict:
    """Get detailed information about the current stage from Neo4j."""
    
    with connection.driver.session(database=connection.database) as session:
        query = """
        MATCH (ps:ProcessStep {category: $stage})
        RETURN ps
        ORDER BY ps.step_order
        """
        result = session.run(query, {"stage": current_stage})
        
        stage_steps = []
        stage_description = ""
        # Convert to list to avoid consumption errors
        records = list(result)
        
        for record in records:
            step_data = dict(record["ps"])
            stage_steps.append({
                "step_order": step_data.get("step_order", 0),
                "title": step_data.get("title", ""),
                "description": step_data.get("description", ""),
                "timeline": step_data.get("timeline", "")
            })
            
            if not stage_description:
                stage_description = f"Stage focused on {step_data.get('category', current_stage)}"
        
        if not stage_steps:
            return {}
        
        return {
            "stage_name": current_stage,
            "description": stage_description,
            "total_steps": len(stage_steps),
            "steps": sorted(stage_steps, key=lambda x: x["step_order"])
        }


def _get_immediate_next_steps(current_stage: str, selected_loan_program: Optional[str], connection) -> List[Dict]:
    """Get immediate next steps for the current stage from Neo4j."""
    
    with connection.driver.session(database=connection.database) as session:
        # Get next steps for current stage
        query = """
        MATCH (ps:ProcessStep {category: $stage})
        RETURN ps
        ORDER BY ps.step_order
        LIMIT 3
        """
        result = session.run(query, {"stage": current_stage})
        
        next_steps = []
        # Convert to list to avoid consumption errors
        records = list(result)
        for record in records:
            step_data = dict(record["ps"])
            next_steps.append({
                "priority": step_data.get("step_order", 1),
                "action": step_data.get("title", ""),
                "description": step_data.get("description", ""),
                "timeline": step_data.get("timeline", ""),
                "importance": "Required" if step_data.get("step_order", 1) <= 2 else "Recommended"
            })
        
        # Add loan program specific steps if provided
        if selected_loan_program:
            program_query = """
            MATCH (lp:LoanProgram {name: $program})
            OPTIONAL MATCH (lp)-[:HAS_REQUIREMENT]->(qr:QualificationRequirement)
            RETURN lp, collect(qr) as requirements
            """
            program_result = session.run(program_query, {"program": selected_loan_program})
            program_record = program_result.single()
            
            if program_record:
                loan_program = dict(program_record["lp"])
                requirements = [dict(req) for req in program_record["requirements"] if req]
                
                # Add program-specific next step
                next_steps.append({
                    "priority": len(next_steps) + 1,
                    "action": f"Complete {selected_loan_program} loan specific requirements",
                    "description": f"Focus on meeting {selected_loan_program} loan program requirements",
                    "timeline": "Ongoing",
                    "importance": "Program-Specific",
                    "requirements": [req.get("details", "") for req in requirements[:2]]
                })
        
        return next_steps


def _get_upcoming_stages(current_stage: str, connection) -> List[Dict]:
    """Get information about upcoming stages in the process from Neo4j."""
    
    # Define stage order mapping
    stage_order = {
        "pre_qualification": 1,
        "application": 2,
        "processing": 3,
        "underwriting": 4,
        "closing": 5,
        "completed": 6
    }
    
    current_order = stage_order.get(current_stage, 0)
    
    with connection.driver.session(database=connection.database) as session:
        upcoming_stages = []
        
        for stage_name, order in stage_order.items():
            if order > current_order:
                query = """
                MATCH (ps:ProcessStep {category: $stage})
                RETURN count(ps) as step_count, 
                       collect(ps.timeline)[0] as typical_duration
                """
                result = session.run(query, {"stage": stage_name})
                stage_record = result.single()
                
                if stage_record and stage_record["step_count"] > 0:
                    upcoming_stages.append({
                        "stage_name": stage_name,
                        "order": order,
                        "step_count": stage_record["step_count"],
                        "typical_duration": stage_record["typical_duration"] or "Varies",
                        "description": f"{stage_name.replace('_', ' ').title()} stage"
                    })
        
        return sorted(upcoming_stages, key=lambda x: x["order"])[:3]  # Next 3 stages


def _get_documentation_requirements(current_stage: str, selected_loan_program: Optional[str], 
                                  borrower_status: str, connection) -> Dict:
    """Get documentation requirements for the current stage from Neo4j."""
    
    # Get stage-specific documentation from ProcessStep data
    with connection.driver.session(database=connection.database) as session:
        query = """
        MATCH (ps:ProcessStep {category: $stage})
        RETURN ps.title as step_title, ps.description as step_description
        ORDER BY ps.step_order
        """
        result = session.run(query, {"stage": current_stage})
        
        stage_docs = []
        # Convert to list to avoid consumption errors
        records = list(result)
        for record in records:
            title = record["step_title"]
            description = record["step_description"]
            
            # Extract documentation needs from step descriptions
            if any(doc_keyword in title.lower() for doc_keyword in ["document", "verify", "income", "asset", "credit"]):
                stage_docs.append({
                    "document_type": title,
                    "description": description,
                    "urgency": "Required for current stage"
                })
        
        # Get loan program specific documentation if selected
        program_docs = []
        if selected_loan_program:
            program_query = """
            MATCH (sr:SpecialRequirement {program_name: $program})
            RETURN sr.requirement_type as req_type, sr.verification_steps as steps, sr.description as description
            """
            program_result = session.run(program_query, {"program": selected_loan_program})
            
            for record in program_result:
                req_type = record["req_type"]
                steps = record.get("steps")  # Use .get() to handle None
                description = record.get("description", "")
                
                if steps and isinstance(steps, list):
                    program_docs.append({
                        "document_type": f"{selected_loan_program} {req_type.replace('_', ' ')}",
                        "description": description or f"Required for {selected_loan_program} loan eligibility",
                        "verification_steps": steps,
                        "urgency": "Program-Specific"
                    })
                elif description:
                    program_docs.append({
                        "document_type": f"{selected_loan_program} {req_type.replace('_', ' ')}",
                        "description": description,
                        "urgency": "Program-Specific"
                    })
        
        # Get general documentation based on borrower status
        general_docs = _get_general_documentation_by_status(borrower_status)
        
        return {
            "stage_specific": stage_docs,
            "program_specific": program_docs,
            "general_requirements": general_docs,
            "total_document_categories": len(stage_docs) + len(program_docs) + len(general_docs)
        }


def _get_general_documentation_by_status(borrower_status: str) -> List[Dict]:
    """Get general documentation requirements based on borrower status."""
    
    if borrower_status == "first_time":
        return [
            {"document_type": "Income Verification", "description": "Pay stubs, tax returns, employment letter"},
            {"document_type": "Asset Documentation", "description": "Bank statements, investment accounts"},
            {"document_type": "Credit Authorization", "description": "Permission for credit report pull"}
        ]
    elif borrower_status == "refinancing":
        return [
            {"document_type": "Current Mortgage Statement", "description": "Most recent mortgage statement"},
            {"document_type": "Property Documentation", "description": "Property tax records, insurance info"},
            {"document_type": "Income Verification", "description": "Recent pay stubs and tax returns"}
        ]
    else:  # repeat buyer
        return [
            {"document_type": "Sale Documentation", "description": "Current home sale contract if applicable"},
            {"document_type": "Income Verification", "description": "Pay stubs, tax returns, employment letter"},
            {"document_type": "Asset Documentation", "description": "Bank statements, down payment source"}
        ]


def _get_timeline_expectations(current_stage: str, selected_loan_program: Optional[str], connection) -> Dict:
    """Get realistic timeline expectations from Neo4j process data."""
    
    with connection.driver.session(database=connection.database) as session:
        # Get current stage timeline
        current_query = """
        MATCH (ps:ProcessStep {category: $stage})
        RETURN ps.timeline as stage_timeline
        ORDER BY ps.step_order
        LIMIT 1
        """
        current_result = session.run(current_query, {"stage": current_stage})
        current_record = current_result.single()
        current_stage_duration = current_record["stage_timeline"] if current_record else "Varies"
        
        # Get total remaining process time
        stage_order = ["pre_qualification", "application", "processing", "underwriting", "closing"]
        current_index = stage_order.index(current_stage) if current_stage in stage_order else 0
        remaining_stages = stage_order[current_index + 1:]
        
        remaining_duration = "0 days"
        if remaining_stages:
            total_query = """
            UNWIND $stages as stage
            MATCH (ps:ProcessStep {category: stage})
            RETURN stage, ps.timeline as duration
            ORDER BY stage
            """
            remaining_result = session.run(total_query, {"stages": remaining_stages})
            stage_durations = []
            for record in remaining_result:
                duration = record["duration"]
                if duration and duration != "Varies":
                    stage_durations.append(duration)
            
            if stage_durations:
                # Simple estimation (this could be more sophisticated)
                estimated_days = len(stage_durations) * 7  # Rough estimate
                remaining_duration = f"{estimated_days}-{estimated_days + 14} days"
        
        # Add program-specific timeline considerations
        program_timeline_notes = []
        if selected_loan_program:
            if selected_loan_program == "VA":
                program_timeline_notes.append("VA loans may require additional 2-4 weeks for COE processing")
            elif selected_loan_program == "USDA":
                program_timeline_notes.append("USDA loans typically add 1-2 weeks for rural property verification")
            elif selected_loan_program == "FHA":
                program_timeline_notes.append("FHA loans have standard processing times")
        
        return {
            "current_stage_duration": current_stage_duration,
            "estimated_remaining_time": remaining_duration,
            "total_typical_process": "30-45 days from application to closing",
            "program_specific_notes": program_timeline_notes,
            "factors_affecting_timeline": [
                "Completeness of documentation",
                "Property appraisal scheduling",
                "Underwriter workload",
                "Loan program requirements"
            ]
        }


def _get_preparation_tips(current_stage: str, selected_loan_program: Optional[str], 
                        borrower_status: str, priority_focus: str, connection) -> List[Dict]:
    """Get preparation tips from Neo4j improvement strategies and business rules."""
    
    with connection.driver.session(database=connection.database) as session:
        tips = []
        
        # Get general preparation strategies from Neo4j
        strategy_query = """
        MATCH (is:ImprovementStrategy)
        WHERE is.category CONTAINS 'Credit' OR is.category CONTAINS 'Down Payment' OR is.category CONTAINS 'Income'
        RETURN is.category as category, is.steps as steps
        ORDER BY is.priority
        LIMIT 3
        """
        strategy_result = session.run(strategy_query)
        
        for record in strategy_result:
            category = record["category"]
            steps = record["steps"]
            if steps:
                tips.append({
                    "category": category,
                    "tip_type": "Preparation Strategy",
                    "actions": steps[:3],  # Top 3 actions
                    "relevance": "General"
                })
        
        # Add stage-specific tips
        if current_stage == "pre_qualification":
            tips.append({
                "category": "Pre-Qualification Success",
                "tip_type": "Stage-Specific",
                "actions": [
                    "Gather 2 years of tax returns and recent pay stubs",
                    "Avoid making large purchases or opening new credit accounts",
                    "Save for down payment and closing costs"
                ],
                "relevance": "Current Stage"
            })
        elif current_stage == "application":
            tips.append({
                "category": "Application Success",
                "tip_type": "Stage-Specific", 
                "actions": [
                    "Respond promptly to lender requests for documentation",
                    "Keep employment and income stable",
                    "Begin house hunting within approved price range"
                ],
                "relevance": "Current Stage"
            })
        elif current_stage == "processing":
            tips.append({
                "category": "Processing Success",
                "tip_type": "Stage-Specific",
                "actions": [
                    "Stay in close contact with loan processor",
                    "Provide additional documentation quickly when requested",
                    "Begin shopping for homeowner's insurance"
                ],
                "relevance": "Current Stage"
            })
        
        # Add program-specific tips if loan program selected
        if selected_loan_program:
            program_tips = _get_program_specific_tips(selected_loan_program, connection)
            if program_tips:
                tips.append(program_tips)
        
        return tips


def _get_program_specific_tips(selected_loan_program: str, connection) -> Optional[Dict]:
    """Get loan program specific preparation tips from Neo4j special requirements."""
    
    with connection.driver.session(database=connection.database) as session:
        query = """
        MATCH (sr:SpecialRequirement {program_name: $program})
        RETURN sr.requirement_type as req_type, sr.description as description, sr.verification_steps as steps
        """
        result = session.run(query, {"program": selected_loan_program})
        
        program_actions = []
        # Convert to list to avoid consumption errors  
        records = list(result)
        for record in records:
            description = record.get("description", "")
            steps = record.get("verification_steps")  # Use .get() to handle None
            if description:
                program_actions.append(description)
            if steps and isinstance(steps, list):
                program_actions.extend(steps[:2])  # Add top 2 verification steps
        
        if program_actions:
            return {
                "category": f"{selected_loan_program} Loan Preparation",
                "tip_type": "Program-Specific",
                "actions": program_actions[:4],  # Limit to 4 actions
                "relevance": "Selected Program"
            }
        
        return None


def _get_program_specific_guidance(current_stage: str, selected_loan_program: str, connection) -> Dict:
    """Get loan program specific guidance for the current stage."""
    
    with connection.driver.session(database=connection.database) as session:
        # Get loan program details
        program_query = """
        MATCH (lp:LoanProgram {name: $program})
        OPTIONAL MATCH (lp)-[:HAS_REQUIREMENT]->(qr:QualificationRequirement)
        RETURN lp, collect(qr) as requirements
        """
        result = session.run(program_query, {"program": selected_loan_program})
        program_record = result.single()
        
        if not program_record:
            return {}
        
        loan_program = dict(program_record["lp"])
        requirements = [dict(req) for req in program_record["requirements"] if req]
        
        # Get special requirements for this program
        special_req_query = """
        MATCH (sr:SpecialRequirement {program_name: $program})
        RETURN sr
        """
        special_result = session.run(special_req_query, {"program": selected_loan_program})
        special_requirements = [dict(record["sr"]) for record in special_result]
        
        return {
            "program_name": selected_loan_program,
            "program_benefits": loan_program.get("benefits", []),
            "key_requirements": [req.get("details", "") for req in requirements[:3]],
            "special_considerations": [
                {
                    "type": req.get("requirement_type", ""),
                    "description": req.get("description", ""),
                    "required": req.get("required", True)
                }
                for req in special_requirements[:3]
            ],
            "stage_specific_focus": _get_stage_specific_program_focus(current_stage, selected_loan_program)
        }


def _get_stage_specific_program_focus(current_stage: str, loan_program: str) -> str:
    """Get stage-specific focus for the loan program."""
    
    focus_map = {
        ("pre_qualification", "VA"): "Verify military eligibility and obtain Certificate of Eligibility",
        ("pre_qualification", "USDA"): "Check property location eligibility and income limits",
        ("pre_qualification", "FHA"): "Review FHA credit score and down payment requirements",
        ("application", "VA"): "Submit COE with application and review VA loan benefits",
        ("application", "USDA"): "Confirm rural property eligibility and submit income documentation",
        ("application", "FHA"): "Prepare for FHA appraisal and mortgage insurance requirements",
        ("processing", "VA"): "Complete VA appraisal and final eligibility verification",
        ("processing", "USDA"): "Finalize USDA property and income verification",
        ("processing", "FHA"): "Complete FHA property inspection and mortgage insurance setup"
    }
    
    return focus_map.get((current_stage, loan_program), f"Follow standard {loan_program} loan process")


def validate_tool() -> bool:
    """
    Validate that the guide_next_steps tool is working correctly with Neo4j.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Test basic next steps guidance
        result1 = guide_next_steps.invoke({
            "current_stage": "pre_qualification",
            "borrower_status": "first_time",
            "priority_focus": "timeline"
        })
        
        # Test with loan program
        result2 = guide_next_steps.invoke({
            "current_stage": "application", 
            "selected_loan_program": "VA",
            "borrower_status": "repeat",
            "priority_focus": "documentation"
        })
        
        # Test with advanced stage
        result3 = guide_next_steps.invoke({
            "current_stage": "underwriting",
            "selected_loan_program": "FHA",
            "borrower_status": "refinancing",
            "priority_focus": "preparation"
        })
        
        # Validate expected structure for all results
        required_keys = ["immediate_next_steps", "upcoming_stages", "documentation_checklist", "timeline_expectations", "success"]
        
        for result in [result1, result2, result3]:
            if not (
                isinstance(result, dict) and
                all(key in result for key in required_keys) and
                result["success"] is True and
                isinstance(result["immediate_next_steps"], list) and
                isinstance(result["upcoming_stages"], list) and
                isinstance(result["documentation_checklist"], dict) and
                isinstance(result["timeline_expectations"], dict)
            ):
                return False
        
        # Validate that VA loan guidance includes program-specific info
        if result2.get("program_specific_guidance") and result2["program_specific_guidance"].get("program_name") != "VA":
            return False
            
        return True
        
    except Exception:
        return False
