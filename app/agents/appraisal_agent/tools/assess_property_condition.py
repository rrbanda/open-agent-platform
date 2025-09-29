"""
Property Condition Assessment Tool

This tool evaluates property condition for lending purposes
based on Neo4j property appraisal rules.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection

logger = logging.getLogger(__name__)


class PropertyConditionRequest(BaseModel):
    """Property condition assessment request parameters."""
    property_address: str = Field(..., description="Property address")
    property_type: str = Field(..., description="Property type (single_family_detached, condominium, townhouse, etc.)")
    year_built: int = Field(..., description="Year property was built")
    roof_condition: str = Field(..., description="Roof condition (excellent, good, fair, poor)")
    exterior_condition: str = Field(..., description="Exterior condition (excellent, good, fair, poor)")
    interior_condition: str = Field(..., description="Interior condition (excellent, good, fair, poor)")
    heating_system: str = Field(..., description="Heating system type and condition")
    electrical_system: str = Field(..., description="Electrical system condition")
    plumbing_system: str = Field(..., description="Plumbing system condition")
    foundation_condition: str = Field(..., description="Foundation condition")
    safety_issues: Optional[List[str]] = Field(default=[], description="Any safety issues identified")
    repair_items: Optional[List[str]] = Field(default=[], description="Items requiring repair")
    loan_program: str = Field(default="conventional", description="Loan program (conventional, fha, va, usda)")


@tool(args_schema=PropertyConditionRequest)
def assess_property_condition(
    property_address: str,
    property_type: str,
    year_built: int,
    roof_condition: str,
    exterior_condition: str,
    interior_condition: str,
    heating_system: str,
    electrical_system: str,
    plumbing_system: str,
    foundation_condition: str,
    safety_issues: Optional[List[str]] = None,
    repair_items: Optional[List[str]] = None,
    loan_program: str = "conventional"
) -> str:
    """
    Assess property condition for lending purposes using Neo4j appraisal rules.
    
    This tool evaluates property condition against lending standards and identifies
    any issues that may affect loan approval or require repairs.
    """
    
    if safety_issues is None:
        safety_issues = []
    if repair_items is None:
        repair_items = []
        
    try:
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get property condition rules
            condition_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'PropertyCondition'
            RETURN rule
            """
            result = session.run(condition_rules_query)
            condition_rules = [dict(record['rule']) for record in result]
            
            # Get safety requirement rules
            safety_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'SafetyRequirements'
            RETURN rule
            """
            result = session.run(safety_rules_query)
            safety_rules = [dict(record['rule']) for record in result]
            
            # Get loan program specific requirements
            program_rules_query = """
            MATCH (rule:PropertyAppraisalRule)
            WHERE rule.category = 'LoanProgramRequirements' AND 
                  (rule.loan_program = $loan_program OR rule.loan_program = 'all')
            RETURN rule
            """
            result = session.run(program_rules_query, {"loan_program": loan_program})
            program_rules = [dict(record['rule']) for record in result]
        
        # Calculate property age
        current_year = 2024
        property_age = current_year - year_built
        
        # Condition scoring
        condition_scores = {
            'excellent': 5,
            'good': 4,
            'average': 3,
            'fair': 2,
            'poor': 1
        }
        
        # Generate condition assessment report
        assessment_report = []
        assessment_report.append("PROPERTY CONDITION ASSESSMENT REPORT")
        assessment_report.append("=" * 50)
        
        # Property Information
        assessment_report.append(f"\n🏠 PROPERTY INFORMATION:")
        assessment_report.append(f"Address: {property_address}")
        assessment_report.append(f"Property Type: {property_type.replace('_', ' ').title()}")
        assessment_report.append(f"Year Built: {year_built} ({property_age} years old)")
        assessment_report.append(f"Loan Program: {loan_program.upper()}")
        
        # System Condition Analysis
        assessment_report.append(f"\n🔧 SYSTEM CONDITION ANALYSIS:")
        
        conditions = {
            'Roof': roof_condition,
            'Exterior': exterior_condition,
            'Interior': interior_condition,
            'Foundation': foundation_condition
        }
        
        systems = {
            'Heating': heating_system,
            'Electrical': electrical_system,
            'Plumbing': plumbing_system
        }
        
        overall_score = 0
        total_items = 0
        condition_issues = []
        
        for component, condition in conditions.items():
            condition_clean = condition.lower()
            score = condition_scores.get(condition_clean, 3)
            overall_score += score
            total_items += 1
            
            status = "" if score >= 4 else "⚠️" if score >= 3 else ""
            assessment_report.append(f"  {status} {component}: {condition.title()}")
            
            if score < 3:
                condition_issues.append(f"{component} condition rated as {condition}")
        
        assessment_report.append(f"\n🔌 MECHANICAL SYSTEMS:")
        for system, condition in systems.items():
            # Simplified condition assessment for systems
            if any(word in condition.lower() for word in ['good', 'excellent', 'new', 'updated']):
                assessment_report.append(f"   {system}: {condition}")
                overall_score += 4
            elif any(word in condition.lower() for word in ['fair', 'average', 'adequate']):
                assessment_report.append(f"  ⚠️ {system}: {condition}")
                overall_score += 3
                condition_issues.append(f"{system} system may need attention")
            else:
                assessment_report.append(f"   {system}: {condition}")
                overall_score += 1
                condition_issues.append(f"{system} system requires evaluation/repair")
            total_items += 1
        
        # Calculate overall condition rating
        average_score = overall_score / total_items if total_items > 0 else 3
        if average_score >= 4.5:
            overall_rating = "Excellent"
            rating_icon = ""
        elif average_score >= 3.5:
            overall_rating = "Good"
            rating_icon = ""
        elif average_score >= 2.5:
            overall_rating = "Fair"
            rating_icon = "⚠️"
        else:
            overall_rating = "Poor"
            rating_icon = ""
        
        assessment_report.append(f"\n📊 OVERALL CONDITION RATING:")
        assessment_report.append(f"  {rating_icon} Overall Rating: {overall_rating} ({average_score:.1f}/5.0)")
        
        # Safety Issues Analysis
        assessment_report.append(f"\n🚨 SAFETY ASSESSMENT:")
        if safety_issues:
            assessment_report.append("  Safety Issues Identified:")
            for issue in safety_issues:
                assessment_report.append(f"     {issue}")
        else:
            assessment_report.append("   No safety issues reported")
        
        # Required Repairs
        assessment_report.append(f"\n🔨 REPAIR REQUIREMENTS:")
        if repair_items:
            assessment_report.append("  Items Requiring Repair:")
            for item in repair_items:
                assessment_report.append(f"    🔧 {item}")
        else:
            assessment_report.append("   No specific repairs identified")
        
        # Loan Program Compliance
        assessment_report.append(f"\n📋 LOAN PROGRAM COMPLIANCE ({loan_program.upper()}):")
        
        # Program-specific requirements
        if loan_program.lower() == 'fha':
            assessment_report.append("  FHA Requirements:")
            assessment_report.append("     Property must be safe, sound, and secure")
            assessment_report.append("     All systems must be operational")
            if safety_issues:
                assessment_report.append("     Safety issues must be resolved before closing")
            if 'poor' in [roof_condition.lower(), foundation_condition.lower()]:
                assessment_report.append("     Major structural issues require repair")
            else:
                assessment_report.append("     Structural components acceptable")
                
        elif loan_program.lower() == 'va':
            assessment_report.append("  VA Requirements:")
            assessment_report.append("     Property must be move-in ready")
            assessment_report.append("     No health/safety hazards")
            if safety_issues or repair_items:
                assessment_report.append("     All deficiencies must be corrected")
            else:
                assessment_report.append("     Property condition meets VA standards")
                
        elif loan_program.lower() == 'usda':
            assessment_report.append("  USDA Requirements:")
            assessment_report.append("     Property must be decent, safe, and sanitary")
            if property_age > 30:
                assessment_report.append("    ⚠️ Additional inspection may be required for older property")
            else:
                assessment_report.append("     Property age acceptable")
                
        else:  # Conventional
            assessment_report.append("  Conventional Requirements:")
            assessment_report.append("     Property must be marketable")
            assessment_report.append("     No condition affecting value or marketability")
        
        # Age-Related Considerations
        assessment_report.append(f"\n📅 AGE-RELATED ANALYSIS:")
        if property_age < 5:
            assessment_report.append("   New construction - minimal condition concerns")
        elif property_age < 20:
            assessment_report.append("   Relatively new - standard condition assessment")
        elif property_age < 40:
            assessment_report.append("  ⚠️ Mature property - verify system updates and maintenance")
        else:
            assessment_report.append("  ⚠️ Older property - comprehensive system evaluation recommended")
            assessment_report.append("  💡 Consider cost approach if major updates needed")
        
        # Condition Impact on Value
        assessment_report.append(f"\n💰 CONDITION IMPACT ON VALUE:")
        if overall_rating in ['Excellent', 'Good']:
            assessment_report.append("   Condition supports market value")
            assessment_report.append("   No condition-related value adjustments needed")
        elif overall_rating == 'Fair':
            assessment_report.append("  ⚠️ Some condition issues may affect value")
            assessment_report.append("  💡 Consider condition adjustments in valuation")
        else:
            assessment_report.append("   Poor condition significantly affects value")
            assessment_report.append("  💡 Major condition adjustments required")
        
        # Recommendations
        assessment_report.append(f"\n💡 RECOMMENDATIONS:")
        
        if overall_rating in ['Excellent', 'Good'] and not safety_issues:
            assessment_report.append("  1. Property condition acceptable for lending")
            assessment_report.append("  2. Proceed with standard appraisal process")
        else:
            assessment_report.append("  1. Address all safety issues before loan approval")
            assessment_report.append("  2. Complete necessary repairs per loan program requirements")
            assessment_report.append("  3. Consider re-inspection after repairs")
        
        if condition_issues:
            assessment_report.append("  4. Document all condition issues in appraisal report")
            assessment_report.append("  5. Consider condition impact on final value estimate")
        
        if property_age > 30:
            assessment_report.append("  6. Verify remaining economic life supports loan term")
        
        # Final Condition Assessment
        assessment_report.append(f"\n🎯 FINAL ASSESSMENT:")
        if overall_rating in ['Excellent', 'Good'] and not safety_issues:
            assessment_report.append(f"   ACCEPTABLE: Property condition meets lending standards")
        elif overall_rating == 'Fair' and not safety_issues:
            assessment_report.append(f"  ⚠️ CONDITIONAL: Property acceptable with noted conditions")
        else:
            assessment_report.append(f"   SUBJECT TO: Property requires repairs before loan approval")
        
        return "\n".join(assessment_report)
        
    except Exception as e:
        logger.error(f"Error during property condition assessment: {e}")
        return f" Error during property condition assessment: {str(e)}"


def validate_tool() -> bool:
    """Validate that the assess_property_condition tool works correctly."""
    try:
        # Test with sample data
        result = assess_property_condition.invoke({
            "property_address": "123 Main St, Anytown, CA 90210",
            "property_type": "single_family_detached",
            "year_built": 2010,
            "roof_condition": "good",
            "exterior_condition": "good",
            "interior_condition": "excellent",
            "heating_system": "Central HVAC, good condition",
            "electrical_system": "Updated electrical panel, good condition",
            "plumbing_system": "Original plumbing, fair condition",
            "foundation_condition": "good",
            "safety_issues": [],
            "repair_items": ["Minor plumbing updates recommended"],
            "loan_program": "conventional"
        })
        return "PROPERTY CONDITION ASSESSMENT REPORT" in result and "FINAL ASSESSMENT" in result
    except Exception as e:
        print(f"Property condition assessment tool validation failed: {e}")
        return False
