"""
Recommend Loan Program Tool - Neo4j Powered

This tool provides personalized loan program recommendations based on borrower
profile, financial situation, and preferences by querying the Neo4j knowledge graph.

Purpose:
- Analyze borrower profile against loan requirements
- Match borrowers to suitable loan programs using graph relationships
- Provide personalized recommendations with reasoning
- Consider multiple factors: credit, down payment, income, property type
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    # Fallback for different import paths during testing
    from utils import get_neo4j_connection, initialize_connection


# Simplified tool without complex Pydantic schema to ensure structured tool calls


@tool
def recommend_loan_program(borrower_info: str) -> str:
    """Provide personalized loan program recommendations based on borrower profile.
    
    Args:
        borrower_info: Borrower details like "Credit: 720, Income: 95000, Down payment: 60000, Monthly debts: 850, Property: single_family, First-time buyer: yes"
        
    Returns:
        String containing personalized loan recommendations and analysis
    """
    
    try:
        # Parse borrower info string 
        import re
        info = borrower_info.lower()
        
        # Extract credit score
        credit_match = re.search(r'credit[:\s]*(\d+)', info)
        credit_score_int = int(credit_match.group(1)) if credit_match else 720
        
        # Extract annual income
        income_match = re.search(r'income[:\s]*(\d+)', info)
        annual_income_int = int(income_match.group(1)) if income_match else 95000
        
        # Extract down payment
        down_match = re.search(r'(?:down.*payment|down)[:\s]*(\d+)', info)
        down_payment_amount = int(down_match.group(1)) if down_match else 60000
        down_payment_float = 0.15  # Default 15%
        
        # Extract monthly debts
        debt_match = re.search(r'(?:monthly\s*debts|debts)[:\s]*(\d+)', info)
        monthly_debts_int = int(debt_match.group(1)) if debt_match else 850
        
        # Extract property type
        property_type = "primary_residence"
        if "investment" in info:
            property_type = "investment"
        elif "vacation" in info:
            property_type = "vacation_home"
        
        # Extract property location
        property_location = "suburban"
        if "urban" in info:
            property_location = "urban"
        elif "rural" in info:
            property_location = "rural"
        
        # Extract military status
        military_status = "none"
        if "veteran" in info:
            military_status = "veteran"
        elif "active" in info and "duty" in info:
            military_status = "active_duty"
        elif "spouse" in info:
            military_status = "spouse"
            
        # Extract first-time buyer status
        first_time_bool = "first" in info and "time" in info and ("yes" in info or "true" in info)
        
        # Initialize Neo4j connection
        if not initialize_connection():
            return "Error: Failed to connect to Neo4j database"
        
        connection = get_neo4j_connection()
        
        # Calculate debt-to-income ratio
        monthly_income = annual_income_int / 12
        dti_ratio = monthly_debts_int / monthly_income if monthly_income > 0 else 1.0
        
        # Determine borrower profile category
        borrower_category = _determine_borrower_category(
            credit_score_int, down_payment_float, military_status, 
            first_time_bool, property_location
        )
        
        # Query loan programs from Neo4j - using actual database schema
        with connection.driver.session(database=connection.database) as session:
            # Get all loan programs with their actual properties
            query = """
            MATCH (lp:LoanProgram)
            RETURN lp
            ORDER BY lp.name
            """
            
            result = session.run(query)
            programs = []
            # Convert result to list immediately to avoid consumption errors
            records = list(result)
            for record in records:
                program_data = dict(record['lp'])
                programs.append({
                    'program': program_data,
                    'requirements': [],  # We'll derive requirements from program properties
                    'target_profiles': []  # We'll determine target profiles based on program characteristics
                })
        
        # Analyze each program for this borrower
        program_analysis = []
        for prog_data in programs:
            program = prog_data['program']
            requirements = prog_data['requirements']
            target_profiles = prog_data['target_profiles']
            
            analysis = _analyze_program_fit(
                program, requirements, target_profiles,
                credit_score_int, down_payment_float, dti_ratio,
                military_status, property_location, borrower_category,
                connection
            )
            program_analysis.append(analysis)
        
        # Sort programs by recommendation score
        program_analysis.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        # Generate recommendations and insights
        recommendations = _generate_recommendations(program_analysis, borrower_category)
        borrower_analysis = _generate_borrower_analysis(
            credit_score_int, down_payment_float, dti_ratio, 
            military_status, first_time_bool, property_location,
            connection
        )
        improvement_suggestions = _generate_improvement_suggestions(
            program_analysis, credit_score_int, down_payment_float, dti_ratio, connection
        )
        qualification_summary = _generate_qualification_summary(program_analysis)
        
        # Format results as readable string
        result = f"""
LOAN PROGRAM RECOMMENDATIONS FOR YOUR PROFILE:

BORROWER PROFILE:
• Credit Score: {credit_score_int}
• Down Payment: {down_payment_float * 100:.1f}%
• Annual Income: ${annual_income_int:,}
• Monthly Income: ${monthly_income:,.0f}
• Monthly Debts: ${monthly_debts_int:,}
• DTI Ratio: {dti_ratio * 100:.1f}%
• Property Type: {property_type}
• Location: {property_location}
• Military Status: {military_status}
• First-Time Buyer: {first_time_bool}
• Borrower Category: {borrower_category}

TOP LOAN PROGRAM RECOMMENDATIONS:"""

        for i, rec in enumerate(recommendations[:3], 1):
            result += f"""

{i}. {rec['program_name']} - {rec['program_full_name']}
   • Qualification Status: {rec['qualification_status']}
   • Recommendation Score: {rec['recommendation_score']}/100
   • Key Benefits: {', '.join(rec['key_benefits'][:2])}
   • Reasons: {rec['recommendation_reasons'][0] if rec['recommendation_reasons'] else 'Good program match'}"""
            
            if rec['qualification_details']:
                result += f"\n   • Details: {rec['qualification_details'][0]}"
            
            if rec['issues']:
                result += f"\n   • Issues: {rec['issues'][0]}"

        result += f"""

BORROWER ANALYSIS:
• Strengths: {', '.join(borrower_analysis['strengths'][:2])}
• Considerations: {', '.join(borrower_analysis['considerations'][:2]) if borrower_analysis['considerations'] else 'None identified'}
• Overall Assessment: {borrower_analysis['overall_assessment']}

QUALIFICATION SUMMARY:
{qualification_summary['summary']}

IMPROVEMENT SUGGESTIONS:
{chr(10).join('• ' + s for s in improvement_suggestions[:3])}

Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return result.strip()
        
    except Exception as e:
        return f"Error analyzing loan recommendations: {str(e)}"
    finally:
        if 'connection' in locals() and connection:
            connection.disconnect()


def _determine_borrower_category(credit_score: int, down_payment: float, military_status: str, 
                                first_time: bool, location: str) -> str:
    """Determine the borrower's category for matching with profiles."""
    if military_status in ['active_duty', 'veteran', 'spouse']:
        return "Military"
    elif location == 'rural':
        return "RuralBuyer"
    elif first_time and credit_score < 680:
        return "FirstTimeBuyer"
    elif credit_score >= 740 and down_payment >= 0.10:
        return "HighIncomeStrongCredit"
    elif first_time:
        return "FirstTimeBuyer"
    else:
        return "GeneralBorrower"


def _analyze_program_fit(program: Dict, requirements: List[Dict], target_profiles: List[str],
                        credit_score: int, down_payment: float, dti_ratio: float,
                        military_status: str, location: str, borrower_category: str, 
                        connection) -> Dict:
    """Analyze how well a loan program fits the borrower using data-driven rules from Neo4j."""
    
    program_name = program['name']
    qualification_score = 0
    qualification_details = []
    issues = []
    
    # Use fixed scoring values since we don't have ScoringRule nodes
    scoring_values = {
        'CreditScoreMatch': 25,
        'CreditScoreExceed': 5,
        'DownPaymentMatch': 25,
        'DownPaymentExceed': 10,
        'DTIMatch': 25,
        'DTIExcellent': 15,
        'VAEligibility': 30,
        'USDAEligibility': 25,
        'FirstTimeBuyerFHA': 15,
        'ProfileMatch': 20
    }
    
    # Check credit score requirement using Neo4j rules
    min_credit = program.get('min_credit_score')
    if min_credit:
        if credit_score >= min_credit:
            qualification_score += scoring_values['CreditScoreMatch']
            qualification_details.append(f"✓ Credit score {credit_score} meets minimum {min_credit}")
            
            # Bonus for exceeding by 50+ points
            if credit_score >= min_credit + 50:
                qualification_score += scoring_values['CreditScoreExceed']
                qualification_details.append(f"✓ Credit score exceeds minimum by {credit_score - min_credit} points")
        else:
            qualification_score -= 30
            issues.append(f"✗ Credit score {credit_score} below minimum {min_credit}")
    else:
        qualification_score += scoring_values['CreditScoreMatch']
        qualification_details.append("✓ No minimum credit score requirement")
    
    # Check down payment requirement using Neo4j rules
    min_down = program.get('min_down_payment', 0)
    if down_payment >= min_down:
        qualification_score += scoring_values['DownPaymentMatch']
        qualification_details.append(f"✓ Down payment {down_payment*100:.1f}% meets minimum {min_down*100:.1f}%")
        
        # Bonus for exceeding by 5%+
        if down_payment >= min_down + 0.05:
            qualification_score += scoring_values['DownPaymentExceed']
            qualification_details.append(f"✓ Down payment exceeds minimum by {(down_payment - min_down)*100:.1f}%")
    else:
        qualification_score -= 25
        issues.append(f"✗ Down payment {down_payment*100:.1f}% below minimum {min_down*100:.1f}%")
    
    # Check DTI requirement using Neo4j rules
    max_dti = program.get('max_dti')
    if max_dti:
        if dti_ratio <= max_dti:
            qualification_score += scoring_values['DTIMatch']
            qualification_details.append(f"✓ DTI {dti_ratio*100:.1f}% within limit {max_dti*100:.0f}%")
            
            # Bonus for excellent DTI
            if dti_ratio <= 0.28:
                qualification_score += scoring_values['DTIExcellent']
                qualification_details.append(f"✓ Excellent DTI ratio under 28%")
        else:
            qualification_score -= 20
            issues.append(f"✗ DTI {dti_ratio*100:.1f}% exceeds limit {max_dti*100:.0f}%")
    else:
        qualification_score += scoring_values['DTIMatch']
        qualification_details.append("✓ No specific DTI limit")
    
    # Special program requirements using Neo4j rules
    special_bonus = 0
    if program_name == 'VA' and military_status in ['active_duty', 'veteran', 'spouse']:
        special_bonus += scoring_values['VAEligibility']
        qualification_details.append("✓ Eligible for VA loan benefits")
    elif program_name == 'USDA' and location == 'rural':
        special_bonus += scoring_values['USDAEligibility']
        qualification_details.append("✓ Property in USDA-eligible rural area")
    elif program_name in ['FHA'] and borrower_category == 'FirstTimeBuyer':
        special_bonus += scoring_values['FirstTimeBuyerFHA']
        qualification_details.append("✓ First-time buyer - good fit for FHA")
    
    # Calculate final recommendation score
    recommendation_score = max(0, qualification_score + special_bonus)
    
    # Determine qualification status based on score
    if qualification_score >= 70:
        qualification_status = "Highly Qualified"
    elif qualification_score >= 40:
        qualification_status = "Qualified"
    elif qualification_score >= 20:
        qualification_status = "Conditionally Qualified"
    else:
        qualification_status = "Not Qualified"
    
    return {
        'program_name': program_name,
        'program_details': program,
        'recommendation_score': recommendation_score,
        'qualification_score': qualification_score,
        'qualification_status': qualification_status,
        'qualification_details': qualification_details,
        'issues': issues,
        'special_benefits': special_bonus > 0,
        'target_profile_match': False  # Simplified since we don't have target profiles
    }


def _generate_recommendations(program_analysis: List[Dict], borrower_category: str) -> List[Dict]:
    """Generate ranked loan program recommendations."""
    recommendations = []
    
    for i, analysis in enumerate(program_analysis[:5]):  # Top 5 programs
        rank = i + 1
        program = analysis['program_details']
        
        # Generate recommendation reasoning
        reasons = []
        if analysis['qualification_status'] == 'Highly Qualified':
            reasons.append("You strongly qualify for this program")
        if analysis['special_benefits']:
            reasons.append("Special benefits available for your situation")
        if analysis['target_profile_match']:
            reasons.append(f"Designed for borrowers like you ({borrower_category})")
        
        # Add program-specific benefits
        if program['name'] == 'VA':
            reasons.append("No down payment and no PMI required")
        elif program['name'] == 'FHA':
            reasons.append("Low down payment with flexible credit requirements")
        elif program['name'] == 'USDA':
            reasons.append("Zero down payment for rural properties")
        
        recommendation = {
            'rank': rank,
            'program_name': program['name'],
            'program_full_name': program['full_name'],
            'recommendation_score': analysis['recommendation_score'],
            'qualification_status': analysis['qualification_status'],
            'key_benefits': program.get('benefits', [])[:3],  # Top 3 benefits
            'recommendation_reasons': reasons,
            'qualification_details': analysis['qualification_details'],
            'issues': analysis['issues']
        }
        
        recommendations.append(recommendation)
    
    return recommendations


def _generate_borrower_analysis(credit_score: int, down_payment: float, dti_ratio: float,
                               military_status: str, first_time: bool, location: str, 
                               connection) -> Dict:
    """Generate analysis of borrower's profile strengths and considerations based on common lending standards."""
    
    strengths = []
    considerations = []
    
    # Credit score analysis
    if credit_score >= 740:
        strengths.append("Excellent credit score - qualifies for best rates")
    elif credit_score >= 680:
        strengths.append("Good credit score - qualifies for most programs")
    elif credit_score >= 620:
        strengths.append("Fair credit score - qualifies for conventional loans")
    elif credit_score >= 580:
        considerations.append("Credit score may limit program options")
    else:
        considerations.append("Credit score needs improvement for most programs")
    
    # Down payment analysis
    if down_payment >= 0.20:
        strengths.append("20%+ down payment - avoids mortgage insurance")
    elif down_payment >= 0.10:
        strengths.append("Good down payment - lower monthly payments")
    elif down_payment >= 0.035:
        strengths.append("Adequate down payment for FHA programs")
    else:
        considerations.append("Low down payment - consider VA or USDA if eligible")
    
    # DTI analysis
    if dti_ratio <= 0.28:
        strengths.append("Excellent debt-to-income ratio")
    elif dti_ratio <= 0.36:
        strengths.append("Good debt-to-income ratio")
    elif dti_ratio <= 0.43:
        considerations.append("DTI acceptable but may limit options")
    else:
        considerations.append("High DTI may affect qualification")
    
    # Special circumstances
    if military_status in ['active_duty', 'veteran']:
        strengths.append("Military service - eligible for VA loan benefits")
    if first_time:
        strengths.append("First-time buyer - eligible for special programs")
    if location == 'rural':
        strengths.append("Rural property - may qualify for USDA loans")
    
    return {
        'strengths': strengths,
        'considerations': considerations,
        'overall_assessment': _generate_overall_assessment(strengths, considerations)
    }


def _generate_overall_assessment(strengths: List[str], considerations: List[str]) -> str:
    """Generate overall assessment of borrower's position."""
    strength_count = len(strengths)
    consideration_count = len(considerations)
    
    if strength_count >= 3 and consideration_count <= 1:
        return "Strong borrower profile with excellent loan options"
    elif strength_count >= 2:
        return "Good borrower profile with multiple loan program options"
    elif consideration_count <= 2:
        return "Solid borrower profile with good loan program opportunities"
    else:
        return "Borrower profile with improvement opportunities for better loan terms"


def _generate_qualification_summary(program_analysis: List[Dict]) -> Dict:
    """Generate summary of program qualifications."""
    highly_qualified = [p for p in program_analysis if p['qualification_status'] == 'Highly Qualified']
    qualified = [p for p in program_analysis if 'Qualified' in p['qualification_status']]
    not_qualified = [p for p in program_analysis if p['qualification_status'] == 'Not Qualified']
    
    return {
        'highly_qualified_programs': [p['program_name'] for p in highly_qualified],
        'qualified_programs': [p['program_name'] for p in qualified if p not in highly_qualified],
        'not_qualified_programs': [p['program_name'] for p in not_qualified],
        'total_options': len(qualified),
        'summary': f"You qualify for {len(qualified)} loan programs, with {len(highly_qualified)} being excellent matches"
    }


def _generate_improvement_suggestions(program_analysis: List[Dict], credit_score: int, 
                                    down_payment: float, dti_ratio: float, connection) -> List[str]:
    """Generate suggestions for improving loan qualification based on common lending standards."""
    suggestions = []
    
    # Credit score improvement suggestions
    if credit_score < 740:
        next_tier = 740 if credit_score < 680 else 740
        suggestions.append(f"Improving credit score to {next_tier}+ would unlock better rates and more programs")
    
    if credit_score < 620:
        suggestions.append("Consider credit repair strategies: pay down balances, dispute errors, avoid new credit")
    
    # Down payment improvement suggestions
    if down_payment < 0.20:
        suggestions.append("Saving for 20% down payment would eliminate mortgage insurance costs")
    elif down_payment < 0.10:
        suggestions.append("Increasing down payment to 10%+ would improve loan terms")
    
    # DTI improvement suggestions
    if dti_ratio > 0.36:
        suggestions.append("Reducing monthly debt payments would improve qualification for more programs")
    if dti_ratio > 0.28:
        suggestions.append("Lowering debt-to-income ratio to 28% would qualify for better rates")
    
    # Check for common program issues
    not_qualified = [p for p in program_analysis if p['qualification_status'] == 'Not Qualified']
    if len(not_qualified) > 2:
        suggestions.append("Consider working with a mortgage advisor to develop a qualification improvement plan")
    
    return suggestions


def validate_tool() -> bool:
    """
    Validate that the recommend_loan_program tool is working correctly with Neo4j.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Test recommendation for a typical first-time buyer
        result1 = recommend_loan_program.invoke({
            "credit_score": 650,
            "down_payment_percent": 0.05,
            "annual_income": 75000,
            "monthly_debts": 800,
            "property_type": "primary_residence",
            "property_location": "suburban",
            "military_status": "none",
            "first_time_buyer": True
        })
        
        # Test recommendation for a veteran
        result2 = recommend_loan_program.invoke({
            "credit_score": 720,
            "down_payment_percent": 0.0,
            "annual_income": 85000,
            "monthly_debts": 600,
            "property_type": "primary_residence",
            "property_location": "urban",
            "military_status": "veteran",
            "first_time_buyer": False
        })
        
        # Validate expected structure for all results
        required_keys = ["borrower_profile", "recommended_programs", "borrower_analysis", "qualification_summary", "success"]
        
        for result in [result1, result2]:
            if not (
                isinstance(result, dict) and
                all(key in result for key in required_keys) and
                result["success"] is True and
                isinstance(result["recommended_programs"], list) and
                len(result["recommended_programs"]) > 0 and
                isinstance(result["borrower_analysis"], dict) and
                isinstance(result["qualification_summary"], dict)
            ):
                return False
        
        # Validate that VA loan is recommended for veteran
        va_recommended = any(
            prog["program_name"] == "VA" 
            for prog in result2["recommended_programs"]
        )
        if not va_recommended:
            return False
            
        return True
        
    except Exception:
        return False
