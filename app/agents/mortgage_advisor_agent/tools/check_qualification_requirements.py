"""
Check Qualification Requirements Tool - Neo4j Powered

This tool analyzes specific qualification requirements for loan programs by querying
the Neo4j knowledge graph to provide detailed requirement analysis and gap identification.

Purpose:
- Analyze qualification requirements for specific loan programs
- Identify gaps between borrower profile and program requirements
- Provide specific guidance on meeting qualification criteria
- Use business rules from Neo4j for dynamic requirement checking
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


class QualificationAnalysisRequest(BaseModel):
    """Schema for qualification requirement analysis"""
    loan_programs: str = Field(
        description="Loan programs to analyze (e.g., 'FHA', 'VA', 'FHA,Conventional'). Use 'all' for all programs"
    )
    borrower_credit_score: Optional[int] = Field(
        description="Borrower's current credit score (300-850)", default=None
    )
    borrower_down_payment: Optional[float] = Field(
        description="Available down payment as percentage (e.g., 0.05 for 5%)", default=None
    )
    borrower_dti_ratio: Optional[float] = Field(
        description="Current debt-to-income ratio as decimal (e.g., 0.30 for 30%)", default=None
    )
    military_status: Optional[str] = Field(
        description="Military status: 'active_duty', 'veteran', 'spouse', 'none'", default="none"
    )
    property_location: Optional[str] = Field(
        description="Property location: 'urban', 'suburban', 'rural'", default="suburban"
    )


@tool("check_qualification_requirements", args_schema=QualificationAnalysisRequest, parse_docstring=True)
def check_qualification_requirements(
    loan_programs: str,
    borrower_credit_score: Optional[int] = None,
    borrower_down_payment: Optional[float] = None,
    borrower_dti_ratio: Optional[float] = None,
    military_status: str = "none",
    property_location: str = "suburban"
) -> Dict[str, Any]:
    """
    Analyze qualification requirements for specific loan programs using Neo4j data.
    
    This tool provides detailed analysis of loan program requirements and identifies
    gaps between borrower profile and qualification criteria using business rules from Neo4j.
    
    Args:
        loan_programs: Loan programs to analyze ('FHA', 'VA', 'Conventional', etc. or 'all')
        borrower_credit_score: Borrower's current credit score (optional)
        borrower_down_payment: Available down payment as percentage (optional)
        borrower_dti_ratio: Current debt-to-income ratio (optional)
        military_status: Military status for VA loan eligibility
        property_location: Property location for USDA eligibility
        
    Returns:
        Dict containing detailed qualification analysis including:
        - program_requirements: detailed requirements for each program
        - qualification_gaps: specific areas where borrower may not meet requirements
        - improvement_roadmap: step-by-step guidance to meet requirements
        - alternative_programs: programs that may be better suited
    """
    
    # Initialize Neo4j connection
    if not initialize_connection():
        return {
            "error": "Failed to connect to Neo4j database",
            "success": False
        }
    
    connection = get_neo4j_connection()
    
    try:
        # Parse requested programs
        if loan_programs.lower() == "all":
            program_names = None  # Will get all programs
        else:
            program_names = [p.strip().upper() for p in loan_programs.split(',')]
        
        # Query loan programs and their requirements from Neo4j
        with connection.driver.session(database=connection.database) as session:
            if program_names:
                query = """
                MATCH (lp:LoanProgram)
                WHERE lp.name IN $program_names
                OPTIONAL MATCH (lp)-[:HAS_REQUIREMENT]->(qr:QualificationRequirement)
                RETURN lp, collect(DISTINCT qr) as requirements
                ORDER BY lp.name
                """
                result = session.run(query, {"program_names": program_names})
            else:
                query = """
                MATCH (lp:LoanProgram)
                OPTIONAL MATCH (lp)-[:HAS_REQUIREMENT]->(qr:QualificationRequirement)
                RETURN lp, collect(DISTINCT qr) as requirements
                ORDER BY lp.name
                """
                result = session.run(query)
            
            # Collect program data - convert result to list to avoid consumption errors
            records = list(result)
            programs_data = []
            for record in records:
                programs_data.append({
                    'program': dict(record['lp']),
                    'requirements': [dict(req) for req in record['requirements'] if req]
                })
        
        if not programs_data:
            available_programs = _get_available_programs(connection)
            return {
                "error": f"No loan programs found for: {loan_programs}",
                "available_programs": available_programs,
                "success": False
            }
        
        # Analyze each program's requirements
        program_analyses = []
        for prog_data in programs_data:
            analysis = _analyze_program_requirements(
                prog_data['program'], prog_data['requirements'],
                borrower_credit_score, borrower_down_payment, borrower_dti_ratio,
                military_status, property_location, connection
            )
            program_analyses.append(analysis)
        
        # Generate qualification gaps and improvement roadmap
        qualification_gaps = _identify_qualification_gaps(program_analyses, connection)
        improvement_roadmap = _generate_improvement_roadmap(qualification_gaps, connection)
        alternative_programs = _suggest_alternative_programs(program_analyses, connection)
        
        return {
            "query_info": {
                "programs_analyzed": [p['program']['name'] for p in programs_data],
                "borrower_provided": {
                    "credit_score": borrower_credit_score,
                    "down_payment": f"{borrower_down_payment * 100:.1f}%" if borrower_down_payment else None,
                    "dti_ratio": f"{borrower_dti_ratio * 100:.1f}%" if borrower_dti_ratio else None,
                    "military_status": military_status,
                    "property_location": property_location
                },
                "timestamp": datetime.now().isoformat()
            },
            "program_requirements": program_analyses,
            "qualification_gaps": qualification_gaps,
            "improvement_roadmap": improvement_roadmap,
            "alternative_programs": alternative_programs,
            "success": True
        }
        
    except Exception as e:
        return {
            "error": f"Error analyzing qualification requirements: {str(e)}",
            "success": False
        }
    finally:
        connection.disconnect()


def _get_available_programs(connection) -> List[str]:
    """Get list of available loan programs from Neo4j"""
    try:
        with connection.driver.session(database=connection.database) as session:
            result = session.run("MATCH (lp:LoanProgram) RETURN lp.name as name ORDER BY name")
            # Convert to list to avoid consumption errors
            records = list(result)
            return [record["name"] for record in records]
    except Exception as e:
        # Return empty list instead of hardcoded fallback - 100% data-driven
        logger.error(f"Failed to get available programs from Neo4j: {e}")
        return []


def _analyze_program_requirements(program: Dict, requirements: List[Dict],
                                credit_score: Optional[int], down_payment: Optional[float], 
                                dti_ratio: Optional[float], military_status: str, 
                                property_location: str, connection) -> Dict:
    """Analyze requirements for a specific program using Neo4j business rules."""
    
    program_name = program['name']
    
    # Get basic program requirements
    basic_requirements = {
        "credit_score": {
            "minimum": program.get('min_credit_score'),
            "description": f"Minimum credit score for {program_name} loans",
            "borrower_meets": None,
            "gap": None
        },
        "down_payment": {
            "minimum": program.get('min_down_payment', 0),
            "minimum_percent": f"{program.get('min_down_payment', 0) * 100:.1f}%",
            "description": f"Minimum down payment for {program_name} loans",
            "borrower_meets": None,
            "gap": None
        },
        "debt_to_income": {
            "maximum": program.get('max_dti'),
            "maximum_percent": f"{program.get('max_dti') * 100:.0f}%" if program.get('max_dti') else None,
            "description": f"Maximum debt-to-income ratio for {program_name} loans",
            "borrower_meets": None,
            "gap": None
        }
    }
    
    # Check borrower against requirements if data provided
    if credit_score is not None and basic_requirements["credit_score"]["minimum"]:
        min_credit = basic_requirements["credit_score"]["minimum"]
        basic_requirements["credit_score"]["borrower_meets"] = credit_score >= min_credit
        if credit_score < min_credit:
            basic_requirements["credit_score"]["gap"] = f"Need {min_credit - credit_score} more points"
    
    if down_payment is not None:
        min_down = basic_requirements["down_payment"]["minimum"]
        basic_requirements["down_payment"]["borrower_meets"] = down_payment >= min_down
        if down_payment < min_down:
            gap_percent = (min_down - down_payment) * 100
            basic_requirements["down_payment"]["gap"] = f"Need {gap_percent:.1f}% more down payment"
    
    if dti_ratio is not None and basic_requirements["debt_to_income"]["maximum"]:
        max_dti = basic_requirements["debt_to_income"]["maximum"]
        basic_requirements["debt_to_income"]["borrower_meets"] = dti_ratio <= max_dti
        if dti_ratio > max_dti:
            gap_percent = (dti_ratio - max_dti) * 100
            basic_requirements["debt_to_income"]["gap"] = f"DTI is {gap_percent:.1f}% too high"
    
    # Get special requirements using Neo4j business rules
    special_requirements = _get_special_requirements(program_name, military_status, property_location, connection)
    
    # Get detailed requirements from Neo4j relationships
    detailed_requirements = []
    for req in requirements:
        detailed_requirements.append({
            "type": req.get('requirement_type', 'General'),
            "minimum_value": req.get('minimum_value'),
            "details": req.get('details', ''),
            "notes": req.get('notes', '')
        })
    
    return {
        "program_name": program_name,
        "program_type": program.get('type', 'Unknown'),
        "summary": program.get('summary', ''),
        "basic_requirements": basic_requirements,
        "special_requirements": special_requirements,
        "detailed_requirements": detailed_requirements,
        "overall_qualification": _determine_overall_qualification(basic_requirements, special_requirements)
    }


def _get_special_requirements(program_name: str, military_status: str, 
                            property_location: str, connection) -> Dict:
    """Get special requirements for specific programs using Neo4j data."""
    
    special_reqs = {}
    
    # Query special requirements from Neo4j - 100% data-driven
    with connection.driver.session(database=connection.database) as session:
        query = """
        MATCH (sr:SpecialRequirement {program_name: $program_name})
        RETURN sr
        ORDER BY sr.requirement_type
        """
        result = session.run(query, {"program_name": program_name})
        # Convert to list to avoid consumption errors
        records = list(result)
        
        for record in records:
            req_data = dict(record["sr"])
            req_type = req_data["requirement_type"]
            
            # Build requirement from Neo4j data
            requirement = {
                "required": req_data.get("required", True),
                "description": req_data.get("description", ""),
                "additional_info": req_data.get("additional_info")
            }
            
            # Check borrower eligibility dynamically based on requirement type
            if req_type == "military_eligibility":
                eligibility_criteria = req_data.get("eligibility_criteria", [])
                requirement["borrower_meets"] = military_status in eligibility_criteria
                if not requirement["borrower_meets"]:
                    requirement["gap"] = req_data.get("gap_message", "Requirement not met")
                    requirement["verification_steps"] = req_data.get("verification_steps", [])
                    
            elif req_type == "property_location":
                eligibility_criteria = req_data.get("eligibility_criteria", [])
                requirement["borrower_meets"] = property_location in eligibility_criteria
                if not requirement["borrower_meets"]:
                    requirement["gap"] = req_data.get("gap_message", "Property location requirement not met")
                    requirement["verification_steps"] = req_data.get("verification_steps", [])
                    
            elif req_type == "va_benefits":
                requirement["benefit_details"] = req_data.get("benefit_details", "")
                
            # Add all other requirements as-is from Neo4j
            special_reqs[req_type] = requirement
    
    return special_reqs


def _determine_overall_qualification(basic_requirements: Dict, special_requirements: Dict) -> Dict:
    """Determine overall qualification status based on requirements analysis."""
    
    meets_basic = True
    issues = []
    
    for req_name, req_data in basic_requirements.items():
        if req_data.get("borrower_meets") is False:
            meets_basic = False
            issues.append(f"{req_name.replace('_', ' ').title()}: {req_data.get('gap', 'Not met')}")
    
    for req_name, req_data in special_requirements.items():
        if req_data.get("borrower_meets") is False:
            meets_basic = False
            issues.append(f"{req_name.replace('_', ' ').title()}: {req_data.get('gap', 'Not met')}")
    
    if meets_basic and not issues:
        status = "Meets All Requirements"
        message = "Borrower appears to meet all basic qualification requirements"
    elif not issues:
        status = "Requirements Not Fully Evaluated"
        message = "Provide borrower information for complete qualification analysis"
    else:
        status = "Has Qualification Gaps"
        message = f"Borrower has {len(issues)} qualification gap(s) to address"
    
    return {
        "status": status,
        "message": message,
        "issues": issues,
        "meets_basic_requirements": meets_basic
    }


def _identify_qualification_gaps(program_analyses: List[Dict], connection) -> Dict:
    """Identify common qualification gaps across programs using Neo4j business rules."""
    
    credit_gaps = []
    down_payment_gaps = []
    dti_gaps = []
    special_gaps = []
    
    for analysis in program_analyses:
        program_name = analysis["program_name"]
        basic_reqs = analysis["basic_requirements"]
        special_reqs = analysis["special_requirements"]
        
        # Collect gaps
        if not basic_reqs["credit_score"].get("borrower_meets", True):
            credit_gaps.append({
                "program": program_name,
                "gap": basic_reqs["credit_score"]["gap"],
                "minimum_required": basic_reqs["credit_score"]["minimum"]
            })
        
        if not basic_reqs["down_payment"].get("borrower_meets", True):
            down_payment_gaps.append({
                "program": program_name,
                "gap": basic_reqs["down_payment"]["gap"],
                "minimum_required": basic_reqs["down_payment"]["minimum_percent"]
            })
        
        if not basic_reqs["debt_to_income"].get("borrower_meets", True):
            dti_gaps.append({
                "program": program_name,
                "gap": basic_reqs["debt_to_income"]["gap"],
                "maximum_allowed": basic_reqs["debt_to_income"]["maximum_percent"]
            })
        
        for req_name, req_data in special_reqs.items():
            if not req_data.get("borrower_meets", True):
                special_gaps.append({
                    "program": program_name,
                    "requirement": req_name,
                    "gap": req_data.get("gap", "Special requirement not met")
                })
    
    return {
        "credit_score_gaps": credit_gaps,
        "down_payment_gaps": down_payment_gaps,
        "debt_to_income_gaps": dti_gaps,
        "special_requirement_gaps": special_gaps,
        "summary": _generate_gap_summary(credit_gaps, down_payment_gaps, dti_gaps, special_gaps)
    }


def _generate_gap_summary(credit_gaps: List, down_payment_gaps: List, 
                         dti_gaps: List, special_gaps: List) -> Dict:
    """Generate summary of qualification gaps."""
    
    total_gaps = len(credit_gaps) + len(down_payment_gaps) + len(dti_gaps) + len(special_gaps)
    
    if total_gaps == 0:
        return {
            "status": "No Qualification Gaps",
            "message": "Borrower meets requirements for all analyzed programs"
        }
    
    gap_types = []
    if credit_gaps:
        gap_types.append(f"credit score ({len(credit_gaps)} programs)")
    if down_payment_gaps:
        gap_types.append(f"down payment ({len(down_payment_gaps)} programs)")
    if dti_gaps:
        gap_types.append(f"debt-to-income ({len(dti_gaps)} programs)")
    if special_gaps:
        gap_types.append(f"special requirements ({len(special_gaps)} programs)")
    
    return {
        "status": "Qualification Gaps Identified",
        "total_gaps": total_gaps,
        "gap_types": gap_types,
        "message": f"Found {total_gaps} qualification gap(s) across {len(gap_types)} requirement area(s)"
    }


def _generate_improvement_roadmap(qualification_gaps: Dict, connection) -> List[Dict]:
    """Generate step-by-step improvement roadmap using Neo4j improvement strategies."""
    
    roadmap = []
    
    # Map gap types to improvement strategy categories
    gap_to_strategy_map = {
        "credit_score_gaps": "Credit Score Improvement",
        "down_payment_gaps": "Down Payment Savings", 
        "debt_to_income_gaps": "Debt-to-Income Reduction"
    }
    
    # Get improvement strategies from Neo4j for relevant gap types
    with connection.driver.session(database=connection.database) as session:
        for gap_type, strategy_category in gap_to_strategy_map.items():
            if qualification_gaps.get(gap_type):
                # Query matching improvement strategy from Neo4j
                query = """
                MATCH (is:ImprovementStrategy {category: $category})
                RETURN is
                """
                result = session.run(query, {"category": strategy_category})
                strategy_record = result.single()
                
                if strategy_record:
                    strategy = dict(strategy_record["is"])
                    gaps = qualification_gaps[gap_type]
                    
                    # Calculate target and impact from actual gaps
                    if gap_type == "credit_score_gaps":
                        highest_credit_needed = max(gap["minimum_required"] for gap in gaps)
                        target = f"Improve credit score to {highest_credit_needed}+"
                        impact = f"Would qualify for {len(gaps)} additional program(s)"
                    elif gap_type == "down_payment_gaps":
                        highest_down_needed = max(float(gap["minimum_required"].rstrip('%')) for gap in gaps)
                        target = f"Save for {highest_down_needed}% down payment"
                        impact = f"Would qualify for {len(gaps)} additional program(s)"
                    else:  # debt_to_income_gaps
                        target = strategy.get("target_description", "Reduce monthly debt payments")
                        impact = f"Would improve qualification for {len(gaps)} program(s)"
                    
                    roadmap.append({
                        "priority": strategy.get("priority", 1),
                        "category": strategy.get("category", ""),
                        "target": target,
                        "steps": strategy.get("steps", []),
                        "timeline": strategy.get("timeline", ""),
                        "impact": impact
                    })
        
        # Handle special requirement gaps with specific strategies
        if qualification_gaps.get("special_requirement_gaps"):
            for gap in qualification_gaps["special_requirement_gaps"]:
                program = gap["program"]
                requirement = gap["requirement"]
                
                # Find matching improvement strategy for special requirements
                if "military_eligibility" in requirement:
                    strategy_query = """
                    MATCH (is:ImprovementStrategy {category: 'VA Loan Eligibility'})
                    RETURN is
                    """
                    result = session.run(strategy_query)
                    strategy_record = result.single()
                    
                    if strategy_record:
                        strategy = dict(strategy_record["is"])
                        roadmap.append({
                            "priority": strategy.get("priority", 3),
                            "category": strategy.get("category", ""),
                            "target": strategy.get("target_description", ""),
                            "steps": strategy.get("steps", []),
                            "timeline": strategy.get("timeline", ""),
                            "impact": strategy.get("impact_description", "")
                        })
                        
                elif "property_location" in requirement and "USDA" in program:
                    strategy_query = """
                    MATCH (is:ImprovementStrategy {category: 'USDA Property Location'})
                    RETURN is
                    """
                    result = session.run(strategy_query)
                    strategy_record = result.single()
                    
                    if strategy_record:
                        strategy = dict(strategy_record["is"])
                        roadmap.append({
                            "priority": strategy.get("priority", 3),
                            "category": strategy.get("category", ""),
                            "target": strategy.get("target_description", ""),
                            "steps": strategy.get("steps", []),
                            "timeline": strategy.get("timeline", ""),
                            "impact": strategy.get("impact_description", "")
                        })
    
    return sorted(roadmap, key=lambda x: x["priority"])


def _suggest_alternative_programs(program_analyses: List[Dict], connection) -> List[Dict]:
    """Suggest alternative programs based on qualification analysis."""
    
    alternatives = []
    
    # Find programs with fewer gaps
    programs_by_gaps = []
    for analysis in program_analyses:
        gap_count = len(analysis["overall_qualification"]["issues"])
        programs_by_gaps.append({
            "program": analysis["program_name"],
            "program_type": analysis["program_type"],
            "gap_count": gap_count,
            "issues": analysis["overall_qualification"]["issues"],
            "meets_requirements": analysis["overall_qualification"]["meets_basic_requirements"]
        })
    
    # Sort by fewest gaps
    programs_by_gaps.sort(key=lambda x: x["gap_count"])
    
    # Suggest top alternatives
    for i, prog in enumerate(programs_by_gaps[:3]):
        if prog["gap_count"] == 0:
            alternatives.append({
                "rank": i + 1,
                "program": prog["program"],
                "type": prog["program_type"],
                "status": "Fully Qualified",
                "reason": "Meets all basic qualification requirements",
                "recommendation": f"Consider {prog['program']} as primary option"
            })
        elif prog["gap_count"] <= 2:
            alternatives.append({
                "rank": i + 1,
                "program": prog["program"],
                "type": prog["program_type"],
                "status": "Nearly Qualified",
                "gaps": prog["issues"],
                "reason": f"Only {prog['gap_count']} requirement gap(s) to address",
                "recommendation": f"Focus on addressing {prog['program']} requirements first"
            })
    
    return alternatives


def validate_tool() -> bool:
    """
    Validate that the check_qualification_requirements tool is working correctly with Neo4j.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Test qualification analysis without borrower data
        result1 = check_qualification_requirements.invoke({
            "loan_programs": "FHA,VA",
            "military_status": "none",
            "property_location": "suburban"
        })
        
        # Test qualification analysis with borrower data
        result2 = check_qualification_requirements.invoke({
            "loan_programs": "VA",
            "borrower_credit_score": 720,
            "borrower_down_payment": 0.0,
            "borrower_dti_ratio": 0.25,
            "military_status": "veteran",
            "property_location": "urban"
        })
        
        # Test analysis with qualification gaps
        result3 = check_qualification_requirements.invoke({
            "loan_programs": "Conventional",
            "borrower_credit_score": 580,
            "borrower_down_payment": 0.02,
            "borrower_dti_ratio": 0.50,
            "military_status": "none",
            "property_location": "suburban"
        })
        
        # Validate expected structure for all results
        required_keys = ["program_requirements", "qualification_gaps", "improvement_roadmap", "success"]
        
        for result in [result1, result2, result3]:
            if not (
                isinstance(result, dict) and
                all(key in result for key in required_keys) and
                result["success"] is True and
                isinstance(result["program_requirements"], list) and
                isinstance(result["qualification_gaps"], dict) and
                isinstance(result["improvement_roadmap"], list)
            ):
                return False
        
        # Validate that veteran with good profile meets VA requirements
        if result2["program_requirements"]:
            va_analysis = result2["program_requirements"][0]
            if va_analysis["overall_qualification"]["status"] != "Meets All Requirements":
                return False
        
        # Validate that poor profile shows gaps
        if not result3["qualification_gaps"]["credit_score_gaps"]:
            return False
            
        return True
        
    except Exception:
        return False
