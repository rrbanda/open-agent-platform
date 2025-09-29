"""
Evaluate Income Sources Tool - Neo4j Powered

This tool performs comprehensive income source evaluation for mortgage underwriting
by querying Neo4j income calculation rules and employment verification criteria.

Purpose:
- Analyze different types of income sources and their usability
- Determine income documentation requirements
- Calculate qualifying income amounts
- Assess income stability and continuity
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


class IncomeSource(BaseModel):
    """Schema for individual income source"""
    income_type: str = Field(description="Type of income: 'w2_salary', 'self_employed', 'rental', 'commission', 'bonus', 'pension', 'social_security', 'disability', etc.")
    monthly_amount: float = Field(description="Monthly income amount from this source")
    years_received: float = Field(description="Years receiving this income", default=2.0)
    employer_name: Optional[str] = Field(description="Employer or income source name", default=None)
    is_continuing: bool = Field(description="Will this income continue for 3+ years?", default=True)


class IncomeEvaluationRequest(BaseModel):
    """Schema for income evaluation request"""
    income_sources: List[IncomeSource] = Field(description="List of all income sources")
    loan_program: str = Field(description="Loan program type: 'conventional', 'fha', 'va', 'usda', 'jumbo'")
    applicant_age: Optional[int] = Field(description="Applicant age (relevant for retirement income)", default=None)


@tool("evaluate_income_sources", args_schema=IncomeEvaluationRequest, parse_docstring=True)
def evaluate_income_sources(
    income_sources: List[Dict[str, Any]],
    loan_program: str,
    applicant_age: Optional[int] = None
) -> str:
    """
    Evaluate and analyze income sources for mortgage underwriting qualification.
    
    This tool analyzes different types of income sources using income calculation
    rules stored in Neo4j to determine usable income and documentation requirements.
    
    Args:
        income_sources: List of income sources with type, amount, and stability info
        loan_program: Loan program type (conventional, fha, va, usda, jumbo)
        applicant_age: Applicant age (relevant for retirement income analysis)
        
    Returns:
        Formatted income evaluation report with qualifying income calculations
    """
    initialize_connection()
    connection = get_neo4j_connection()
    
    try:
        # Query income calculation rules
        income_rules_query = """
        MATCH (r:IncomeCalculationRule)
        RETURN r
        ORDER BY r.rule_id
        """
        
        with connection.driver.session(database=connection.database) as session:
            result = session.run(income_rules_query)
            income_rules = [dict(record['r']) for record in result]
        
        if not income_rules:
            return " No income calculation rules found in Neo4j. Please load income rules first."
        
        # Convert income_sources to proper format if needed
        if income_sources and isinstance(income_sources[0], dict):
            # Already in dict format, convert to IncomeSource objects for validation
            validated_sources = []
            for source in income_sources:
                validated_sources.append(IncomeSource(**source))
            income_sources = validated_sources
        
        # Evaluate each income source
        source_evaluations = []
        total_qualifying_income = 0.0
        
        for source in income_sources:
            evaluation = _evaluate_single_income_source(source, income_rules, loan_program, applicant_age)
            source_evaluations.append(evaluation)
            total_qualifying_income += evaluation["qualifying_monthly_amount"]
        
        # Analyze overall income profile
        income_profile = _analyze_income_profile(source_evaluations, income_rules)
        
        # Generate documentation requirements
        documentation_requirements = _generate_documentation_requirements(source_evaluations, income_rules)
        
        # Generate recommendations
        recommendations = _generate_income_recommendations(
            source_evaluations, income_profile, total_qualifying_income, loan_program
        )
        
        return _format_income_evaluation_report(
            source_evaluations, income_profile, total_qualifying_income, 
            documentation_requirements, recommendations, loan_program
        )
        
    except Exception as e:
        return f" Error during income evaluation: {str(e)}"


def _evaluate_single_income_source(
    source: IncomeSource, 
    rules: List[Dict], 
    loan_program: str,
    applicant_age: Optional[int]
) -> Dict[str, Any]:
    """Evaluate a single income source against underwriting rules."""
    
    evaluation = {
        "income_type": source.income_type,
        "stated_monthly_amount": source.monthly_amount,
        "qualifying_monthly_amount": 0.0,
        "usability_percentage": 0.0,
        "stability_rating": "unknown",
        "documentation_required": [],
        "issues": [],
        "employer_name": source.employer_name
    }
    
    # Find applicable rules for this income type
    applicable_rules = [r for r in rules if source.income_type in r.get("income_types", [])]
    
    if not applicable_rules:
        # Default evaluation for unknown income types
        evaluation["qualifying_monthly_amount"] = source.monthly_amount * 0.75  # Conservative approach
        evaluation["usability_percentage"] = 75.0
        evaluation["stability_rating"] = "needs_review"
        evaluation["issues"].append(f"No specific rules found for {source.income_type}")
        return evaluation
    
    # Apply the most relevant rule
    best_rule = applicable_rules[0]  # Take first matching rule
    
    try:
        # Calculate usability percentage
        usability_factors = json.loads(best_rule.get("usability_factors", "{}"))
        base_usability = usability_factors.get("base_percentage", 100)
        
        # Apply stability adjustments
        if source.years_received < 2.0:
            stability_penalty = usability_factors.get("short_history_penalty", 25)
            base_usability -= stability_penalty
            evaluation["issues"].append(f"Income history less than 2 years reduces usability by {stability_penalty}%")
        
        # Apply continuity adjustments
        if not source.is_continuing:
            continuity_penalty = usability_factors.get("non_continuing_penalty", 50)
            base_usability -= continuity_penalty
            evaluation["issues"].append(f"Non-continuing income reduces usability by {continuity_penalty}%")
        
        # Special handling for specific income types
        if source.income_type == "bonus" or source.income_type == "commission":
            if source.years_received < 2.0:
                base_usability = 0  # Cannot use bonus/commission with less than 2 years
                evaluation["issues"].append("Bonus/commission income requires 2+ year history")
        
        elif source.income_type == "rental":
            vacancy_factor = usability_factors.get("vacancy_factor", 25)
            base_usability = min(base_usability, 75)  # Max 75% for rental income
            evaluation["issues"].append(f"Rental income reduced by {vacancy_factor}% vacancy factor")
        
        elif source.income_type == "self_employed":
            if source.years_received < 2.0:
                base_usability = 0  # Self-employed requires 2+ years
                evaluation["issues"].append("Self-employed income requires 2+ year tax return history")
            else:
                # Use average of last 2 years, declining trend analysis needed
                trend_adjustment = usability_factors.get("trend_adjustment", 0)
                base_usability += trend_adjustment
        
        elif source.income_type in ["social_security", "pension", "disability"]:
            if applicant_age and applicant_age >= 62:
                base_usability = 100  # Full usability for retirement-age applicants
            else:
                continuation_requirement = best_rule.get("continuation_years", 3)
                if source.is_continuing:
                    base_usability = 100
                else:
                    evaluation["issues"].append(f"Requires {continuation_requirement}+ years continuation")
        
        # Ensure usability is between 0 and 100
        base_usability = max(0, min(100, base_usability))
        
        evaluation["usability_percentage"] = base_usability
        evaluation["qualifying_monthly_amount"] = source.monthly_amount * (base_usability / 100)
        
        # Determine stability rating
        if base_usability >= 90:
            evaluation["stability_rating"] = "excellent"
        elif base_usability >= 75:
            evaluation["stability_rating"] = "good"
        elif base_usability >= 50:
            evaluation["stability_rating"] = "fair"
        elif base_usability > 0:
            evaluation["stability_rating"] = "poor"
        else:
            evaluation["stability_rating"] = "unusable"
        
        # Documentation requirements
        doc_requirements = best_rule.get("required_documentation", [])
        evaluation["documentation_required"] = doc_requirements
        
    except Exception as e:
        # Fallback evaluation
        evaluation["qualifying_monthly_amount"] = source.monthly_amount * 0.5
        evaluation["usability_percentage"] = 50.0
        evaluation["stability_rating"] = "needs_manual_review"
        evaluation["issues"].append(f"Error in rule application: {str(e)}")
    
    return evaluation


def _analyze_income_profile(evaluations: List[Dict], rules: List[Dict]) -> Dict[str, Any]:
    """Analyze the overall income profile."""
    
    profile = {
        "primary_income_types": [],
        "income_diversity": "low",
        "overall_stability": "good",
        "risk_factors": [],
        "strengths": []
    }
    
    # Identify primary income types (>25% of total)
    total_income = sum(eval["qualifying_monthly_amount"] for eval in evaluations)
    
    for evaluation in evaluations:
        if total_income > 0:
            percentage = (evaluation["qualifying_monthly_amount"] / total_income) * 100
            if percentage >= 25:
                profile["primary_income_types"].append({
                    "type": evaluation["income_type"],
                    "percentage": round(percentage, 1)
                })
    
    # Assess income diversity
    unique_types = len(set(eval["income_type"] for eval in evaluations))
    if unique_types == 1:
        profile["income_diversity"] = "low"
    elif unique_types == 2:
        profile["income_diversity"] = "medium"
    else:
        profile["income_diversity"] = "high"
    
    # Assess overall stability
    stability_scores = {"excellent": 4, "good": 3, "fair": 2, "poor": 1, "unusable": 0}
    avg_stability = sum(stability_scores.get(eval["stability_rating"], 0) for eval in evaluations) / len(evaluations)
    
    if avg_stability >= 3.5:
        profile["overall_stability"] = "excellent"
    elif avg_stability >= 2.5:
        profile["overall_stability"] = "good"
    elif avg_stability >= 1.5:
        profile["overall_stability"] = "fair"
    else:
        profile["overall_stability"] = "poor"
    
    # Identify risk factors and strengths
    for evaluation in evaluations:
        if evaluation["issues"]:
            profile["risk_factors"].extend(evaluation["issues"])
        
        if evaluation["stability_rating"] in ["excellent", "good"]:
            profile["strengths"].append(f"{evaluation['income_type']} income is well-established")
    
    return profile


def _generate_documentation_requirements(evaluations: List[Dict], rules: List[Dict]) -> List[str]:
    """Generate comprehensive documentation requirements."""
    
    all_docs = set()
    
    for evaluation in evaluations:
        all_docs.update(evaluation["documentation_required"])
    
    # Add standard documentation
    all_docs.update(["pay_stubs_recent_30_days", "employment_verification"])
    
    return sorted(list(all_docs))


def _generate_income_recommendations(
    evaluations: List[Dict],
    profile: Dict,
    total_qualifying_income: float,
    loan_program: str
) -> List[str]:
    """Generate income-based underwriting recommendations."""
    
    recommendations = []
    
    # Overall income assessment
    if total_qualifying_income > 0:
        recommendations.append(f" Total qualifying monthly income: ${total_qualifying_income:,.2f}")
    else:
        recommendations.append(" No qualifying income identified")
        return recommendations
    
    # Stability assessment
    if profile["overall_stability"] == "excellent":
        recommendations.append(" Excellent income stability - strong approval likelihood")
    elif profile["overall_stability"] == "good":
        recommendations.append(" Good income stability - meets underwriting standards")
    elif profile["overall_stability"] == "fair":
        recommendations.append("⚠️ Fair income stability - may need compensating factors")
    else:
        recommendations.append(" Poor income stability - consider improving before applying")
    
    # Diversity assessment
    if profile["income_diversity"] == "high":
        recommendations.append(" Diversified income sources reduce risk")
    elif profile["income_diversity"] == "low":
        recommendations.append("⚠️ Single income source - ensure stability documentation")
    
    # Risk factor recommendations
    if profile["risk_factors"]:
        recommendations.append("⚠️ Income risk factors identified:")
        for risk in profile["risk_factors"][:3]:  # Limit to top 3
            recommendations.append(f"  • {risk}")
    
    # Income type specific recommendations
    for evaluation in evaluations:
        if evaluation["stability_rating"] == "unusable":
            recommendations.append(f" {evaluation['income_type']} income cannot be used - consider alternatives")
        elif evaluation["stability_rating"] == "poor":
            recommendations.append(f"⚠️ {evaluation['income_type']} income has limited usability")
    
    # Program-specific advice
    if loan_program == "va":
        recommendations.append("💡 VA loans consider residual income - stable income crucial")
    elif loan_program == "usda":
        recommendations.append("💡 USDA loans have income limits - verify geographic eligibility")
    
    return recommendations


def _format_income_evaluation_report(
    evaluations: List[Dict],
    profile: Dict,
    total_qualifying_income: float,
    documentation_requirements: List[str],
    recommendations: List[str],
    loan_program: str
) -> str:
    """Format the comprehensive income evaluation report."""
    
    report = f"""
💰 **Income Source Evaluation Report**

**Loan Program:** {loan_program.upper()}
**Total Qualifying Income:** ${total_qualifying_income:,.2f}/month
**Overall Stability:** {profile['overall_stability'].title()}
**Income Diversity:** {profile['income_diversity'].title()}

📊 **Individual Income Source Analysis:**
"""
    
    for i, evaluation in enumerate(evaluations, 1):
        stability_emoji = {
            "excellent": "🟢",
            "good": "🟡", 
            "fair": "🟠",
            "poor": "🔴",
            "unusable": "⚫"
        }
        
        report += f"""
{i}. **{evaluation['income_type'].replace('_', ' ').title()}**
   • Stated Amount: ${evaluation['stated_monthly_amount']:,.2f}/month
   • Qualifying Amount: ${evaluation['qualifying_monthly_amount']:,.2f}/month
   • Usability: {evaluation['usability_percentage']:.1f}%
   • Stability: {stability_emoji.get(evaluation['stability_rating'], '⚪')} {evaluation['stability_rating'].title()}
"""
        if evaluation["employer_name"]:
            report += f"   • Employer: {evaluation['employer_name']}\n"
        
        if evaluation["issues"]:
            report += "   • Issues:\n"
            for issue in evaluation["issues"]:
                report += f"     - {issue}\n"
    
    # Primary income sources
    if profile["primary_income_types"]:
        report += "\n🎯 **Primary Income Sources:**\n"
        for primary in profile["primary_income_types"]:
            report += f"• {primary['type'].replace('_', ' ').title()}: {primary['percentage']:.1f}% of total\n"
    
    # Documentation requirements
    report += f"\n📋 **Documentation Requirements ({len(documentation_requirements)} items):**\n"
    for doc in documentation_requirements[:8]:  # Limit display
        report += f"• {doc.replace('_', ' ').title()}\n"
    if len(documentation_requirements) > 8:
        report += f"• ... and {len(documentation_requirements) - 8} more items\n"
    
    # Recommendations
    report += "\n💡 **Recommendations:**\n"
    for rec in recommendations:
        report += f"{rec}\n"
    
    report += """
---
**Next Steps:** Gather required documentation and verify income stability
"""
    
    return report


def validate_tool() -> bool:
    """Validate that the evaluate_income_sources tool works correctly."""
    try:
        # Test with sample data
        sample_sources = [
            {
                "income_type": "w2_salary",
                "monthly_amount": 6000.0,
                "years_received": 3.0,
                "employer_name": "Tech Corp",
                "is_continuing": True
            },
            {
                "income_type": "bonus",
                "monthly_amount": 500.0,
                "years_received": 2.5,
                "employer_name": "Tech Corp",
                "is_continuing": True
            }
        ]
        
        result = evaluate_income_sources.invoke({
            "income_sources": sample_sources,
            "loan_program": "conventional",
            "applicant_age": 35
        })
        return "Income Source Evaluation Report" in result and "Total Qualifying Income" in result
    except Exception as e:
        print(f"Income evaluation tool validation failed: {e}")
        return False


if __name__ == "__main__":
    # Test the tool
    print("Testing evaluate_income_sources tool...")
    result = validate_tool()
    print(f"Validation result: {result}")
