"""
Explain Loan Programs Tool - Neo4j Powered

This tool queries real mortgage loan program data from Neo4j to provide
comprehensive education about different loan programs, their requirements,
benefits, and ideal use cases.

Purpose:
- Query Neo4j for loan program information
- Compare different loan programs side-by-side
- Provide personalized recommendations based on data relationships
- Deliver dynamic, up-to-date mortgage guidance
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


class LoanProgramQuery(BaseModel):
    """Schema for loan program explanation queries"""
    programs: str = Field(
        description="Loan programs to explain (e.g., 'FHA', 'VA', 'Conventional', 'all'). Can be single program or comma-separated list"
    )
    comparison_focus: Optional[str] = Field(
        description="Specific aspect to focus comparison on (e.g., 'down_payment', 'credit_requirements', 'benefits')",
        default=None
    )


@tool("explain_loan_programs", args_schema=LoanProgramQuery, parse_docstring=True)
def explain_loan_programs(programs: str, comparison_focus: Optional[str] = None) -> Dict[str, Any]:
    """
    Explain and compare mortgage loan programs using real data from Neo4j.
    
    This tool queries the Neo4j knowledge graph to provide comprehensive
    education about mortgage loan programs, including requirements, benefits,
    and ideal use cases.
    
    Args:
        programs: Loan programs to explain (FHA, VA, USDA, Conventional, Jumbo, or 'all')
        comparison_focus: Optional focus area for comparison (down_payment, credit_requirements, benefits)
        
    Returns:
        Dict containing detailed loan program information from Neo4j including:
        - program_details: comprehensive information for each program
        - comparison_summary: side-by-side comparison when multiple programs
        - recommendations: guidance on which programs might be suitable
        - borrower_profiles: matching borrower profiles from knowledge graph
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
        if programs.lower() == "all":
            program_names = None  # Will get all programs
        else:
            program_names = [p.strip().upper() for p in programs.split(',')]
        
        # Query loan programs from Neo4j using session
        with connection.driver.session(database=connection.database) as session:
            if program_names:
                # Query specific programs
                query = """
                MATCH (lp:LoanProgram)
                WHERE lp.name IN $program_names
                OPTIONAL MATCH (lp)-[:HAS_REQUIREMENT]->(qr:QualificationRequirement)
                OPTIONAL MATCH (bp:BorrowerProfile)-[:RECOMMENDED_FOR]->(lp)
                RETURN lp, collect(DISTINCT qr) as requirements, collect(DISTINCT bp) as profiles
                ORDER BY lp.name
                """
                result = session.run(query, {"program_names": program_names})
            else:
                # Query all programs
                query = """
                MATCH (lp:LoanProgram)
                OPTIONAL MATCH (lp)-[:HAS_REQUIREMENT]->(qr:QualificationRequirement)
                OPTIONAL MATCH (bp:BorrowerProfile)-[:RECOMMENDED_FOR]->(lp)
                RETURN lp, collect(DISTINCT qr) as requirements, collect(DISTINCT bp) as profiles
                ORDER BY lp.name
                """
                result = session.run(query)
            
            # Process query results
            program_details = {}
            all_programs = []
            
            # Convert Neo4j records to dictionaries - consume result immediately
            records = []
            for record in result:
                records.append(record)
        
        for record in records:
            loan_program = dict(record["lp"])
            requirements = [dict(req) for req in record["requirements"] if req]
            profiles = [dict(prof) for prof in record["profiles"] if prof]
            
            program_name = loan_program["name"]
            all_programs.append(program_name)
            
            # Structure the program data
            program_details[program_name] = {
                "basic_info": {
                    "name": loan_program["name"],
                    "full_name": loan_program["full_name"],
                    "type": loan_program["type"],
                    "summary": loan_program["summary"]
                },
                "requirements": {
                    "min_credit_score": loan_program.get("min_credit_score"),
                    "min_down_payment": f"{loan_program.get('min_down_payment', 0) * 100:.1f}%",
                    "max_dti": f"{loan_program.get('max_dti', 0) * 100:.0f}%" if loan_program.get('max_dti') else None,
                    "mortgage_insurance_required": loan_program.get("mortgage_insurance_required"),
                    "detailed_requirements": requirements
                },
                "benefits": loan_program.get("benefits", []),
                "drawbacks": loan_program.get("drawbacks", []),
                "best_for": loan_program.get("best_for", []),
                "recommended_borrower_profiles": [prof["profile_name"] for prof in profiles]
            }
        
        if not program_details:
            available_programs = _get_available_programs(connection)
            return {
                "error": f"No loan programs found for: {programs}",
                "available_programs": available_programs,
                "success": False
            }
        
        # Create comparison summary if multiple programs
        comparison_summary = None
        if len(program_details) > 1:
            comparison_summary = _create_comparison_summary(program_details, comparison_focus)
        
        # Generate recommendations based on Neo4j relationships
        recommendations = _generate_neo4j_recommendations(connection, all_programs)
        
        # Get borrower profile insights
        borrower_insights = _get_borrower_profile_insights(connection, all_programs)
        
        return {
            "query": {
                "programs_requested": all_programs,
                "comparison_focus": comparison_focus,
                "timestamp": datetime.now().isoformat()
            },
            "program_details": program_details,
            "comparison_summary": comparison_summary,
            "recommendations": recommendations,
            "borrower_insights": borrower_insights,
            "key_takeaways": _generate_key_takeaways(program_details),
            "success": True
        }
        
    except Exception as e:
        return {
            "error": f"Error querying Neo4j: {str(e)}",
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
        # If Neo4j query fails, return empty list instead of hardcoded fallback
        logger.error(f"Failed to get available programs from Neo4j: {e}")
        return []


def _create_comparison_summary(program_details: Dict, focus: Optional[str]) -> Dict[str, Any]:
    """Create a comparison summary for multiple programs"""
    
    if focus == "down_payment":
        comparison = {
            "focus": "Down Payment Requirements",
            "comparison": {}
        }
        for program, details in program_details.items():
            comparison["comparison"][program] = {
                "minimum_down": details["requirements"]["min_down_payment"],
                "mortgage_insurance": details["requirements"]["mortgage_insurance_required"]
            }
    elif focus == "credit_requirements":
        comparison = {
            "focus": "Credit Score Requirements", 
            "comparison": {}
        }
        for program, details in program_details.items():
            comparison["comparison"][program] = {
                "minimum_credit": details["requirements"]["min_credit_score"],
                "type": details["basic_info"]["type"]
            }
    else:
        # General comparison
        comparison = {
            "focus": "General Comparison",
            "comparison": {}
        }
        for program, details in program_details.items():
            comparison["comparison"][program] = {
                "type": details["basic_info"]["type"],
                "min_credit": details["requirements"]["min_credit_score"],
                "min_down": details["requirements"]["min_down_payment"],
                "key_benefit": details["benefits"][0] if details["benefits"] else "No specific benefits listed"
            }
    
    return comparison


def _generate_neo4j_recommendations(connection, programs: List[str]) -> List[str]:
    """Generate recommendations based on Neo4j relationships and data"""
    recommendations = []
    
    try:
        # Get smart recommendations based on relationships in the graph
        with connection.driver.session(database=connection.database) as session:
            query = """
            MATCH (lp:LoanProgram)
            WHERE lp.name IN $programs
            OPTIONAL MATCH (bp:BorrowerProfile)-[:RECOMMENDED_FOR]->(lp)
            RETURN lp.name as program, 
                   lp.type as type,
                   lp.min_credit_score as min_credit,
                   lp.min_down_payment as min_down,
                   collect(bp.profile_name) as profiles
            ORDER BY lp.name
            """
            
            result = session.run(query, {"programs": programs})
            records = []
            for record in result:
                records.append(record)
        
        for record in records:
            program = record["program"]
            program_type = record["type"]
            min_credit = record["min_credit"]
            min_down = record["min_down"]
            profiles = record["profiles"]
            
            if program_type == "Government-backed":
                if min_down == 0.0:
                    recommendations.append(f"{program} offers zero down payment, perfect for buyers with limited savings")
                elif min_down <= 0.035:
                    recommendations.append(f"{program} requires only {min_down*100:.1f}% down payment, great for first-time buyers")
            
            if min_credit and min_credit <= 580:
                recommendations.append(f"{program} accepts lower credit scores (as low as {min_credit}), helping more borrowers qualify")
            
            if profiles:
                profile_desc = ", ".join(profiles)
                recommendations.append(f"{program} is recommended for: {profile_desc}")
        
        # Add general guidance
        if len(programs) > 1:
            recommendations.append("Compare total costs over the life of the loan, not just down payment requirements")
            recommendations.append("Consider your long-term financial goals when choosing between programs")
            
    except Exception:
        # Fallback recommendations if query fails
        recommendations = [
            "Each loan program has different qualification requirements and benefits",
            "Consider your credit score, down payment amount, and property location when choosing",
            "Government-backed loans often have lower down payment requirements",
            "Conventional loans offer more flexibility but typically require higher credit scores"
        ]
    
    return recommendations


def _get_borrower_profile_insights(connection, programs: List[str]) -> Dict[str, Any]:
    """Get borrower profile insights from Neo4j relationships"""
    try:
        with connection.driver.session(database=connection.database) as session:
            query = """
            MATCH (bp:BorrowerProfile)-[:RECOMMENDED_FOR]->(lp:LoanProgram)
            WHERE lp.name IN $programs
            RETURN bp.profile_name as profile,
                   bp.description as description,
                   bp.typical_credit_range as credit_range,
                   bp.typical_down_payment as down_payment,
                   collect(lp.name) as recommended_programs,
                   bp.key_considerations as considerations
            ORDER BY bp.profile_name
            """
            
            result = session.run(query, {"programs": programs})
            records = []
            for record in result:
                records.append(record)
        
        insights = {}
        for record in records:
            profile_name = record["profile"]
            insights[profile_name] = {
                "description": record["description"],
                "typical_credit_range": record["credit_range"],
                "typical_down_payment": record["down_payment"],
                "recommended_programs": record["recommended_programs"],
                "key_considerations": record["considerations"]
            }
        
        return insights
        
    except Exception:
        return {}


def _generate_key_takeaways(program_details: Dict) -> List[str]:
    """Generate key takeaways based on the programs discussed"""
    takeaways = []
    
    if len(program_details) == 1:
        program_name = list(program_details.keys())[0]
        program = program_details[program_name]
        takeaways = [
            program["basic_info"]["summary"],
            f"Minimum credit score: {program['requirements']['min_credit_score'] or 'No minimum specified'}",
            f"Minimum down payment: {program['requirements']['min_down_payment']}",
            f"Key benefit: {program['benefits'][0] if program['benefits'] else 'Government backing'}"
        ]
    else:
        # Multiple programs
        gov_backed = [name for name, details in program_details.items() if details["basic_info"]["type"] == "Government-backed"]
        conventional = [name for name, details in program_details.items() if details["basic_info"]["type"] == "Non-government"]
        
        takeaways = [
            "Each loan program serves different borrower needs and circumstances",
            f"Government-backed programs ({', '.join(gov_backed)}) often have lower down payment requirements" if gov_backed else "",
            f"Conventional programs ({', '.join(conventional)}) offer more flexibility but higher credit requirements" if conventional else "",
            "Consider your credit score, down payment savings, and property type when choosing",
            "Factor in mortgage insurance costs and total loan costs, not just down payment"
        ]
        takeaways = [t for t in takeaways if t]  # Remove empty strings
    
    return takeaways


def validate_tool() -> bool:
    """
    Validate that the explain_loan_programs tool is working correctly with Neo4j.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Test single program explanation
        result1 = explain_loan_programs.invoke({
            "programs": "FHA",
            "comparison_focus": None
        })
        
        # Test multiple program comparison
        result2 = explain_loan_programs.invoke({
            "programs": "FHA,VA,Conventional",
            "comparison_focus": "down_payment"
        })
        
        # Test all programs
        result3 = explain_loan_programs.invoke({
            "programs": "all",
            "comparison_focus": "credit_requirements"
        })
        
        # Validate expected structure for all results
        required_keys = ["program_details", "recommendations", "key_takeaways", "success"]
        
        for result in [result1, result2, result3]:
            if not (
                isinstance(result, dict) and
                all(key in result for key in required_keys) and
                result["success"] is True and
                isinstance(result["program_details"], dict) and
                isinstance(result["recommendations"], list) and
                isinstance(result["key_takeaways"], list)
            ):
                return False
        
        # Validate comparison summary exists for multiple programs
        if not (result2.get("comparison_summary") and result3.get("comparison_summary")):
            return False
            
        return True
        
    except Exception:
        return False
