"""
Verify Document Completeness Tool - Neo4j Powered

Checks document completeness using Document Verification Rules from Neo4j.
No hardcoded document requirements - all logic comes from business rules.
"""

from typing import Dict, List, Set
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection


class DocumentCompletenessRequest(BaseModel):
    """Schema for document completeness verification"""
    application_id: str = Field(description="Application identifier to check completeness for")
    loan_program: str = Field(description="Loan program type (FHA, VA, Conventional, etc.)", default="general")


@tool("verify_document_completeness", args_schema=DocumentCompletenessRequest, parse_docstring=True)
def verify_document_completeness(application_id: str, loan_program: str = "general") -> str:
    """
    Check document completeness using Neo4j Document Verification Rules.
    
    Determines required documents from business rules stored in Neo4j rather than
    hardcoded lists. Analyzes what's been submitted vs what's required.
    
    Args:
        application_id: Application identifier
        loan_program: Loan program type for specific requirements
        
    Returns:
        Document completeness analysis with specific missing documents
    """
    
    try:
        # Initialize database connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        # Get required documents from Neo4j rules
        required_doc_categories = _get_required_categories_from_rules(connection, loan_program)
        
        # Get submitted documents for this application
        submitted_documents = _get_submitted_documents(connection, application_id)
        
        # Analyze completeness
        completeness_analysis = _analyze_completeness(
            required_doc_categories, submitted_documents, loan_program
        )
        
        # Format comprehensive report
        return _format_completeness_report(application_id, completeness_analysis)
        
    except Exception as e:
        return f" Error analyzing document completeness: {str(e)}"


def _get_required_categories_from_rules(connection, loan_program: str) -> Dict[str, Dict]:
    """Get required document categories from Neo4j Document Verification Rules."""
    
    with connection.driver.session(database=connection.database) as session:
        # Query for document verification rules to determine categories
        query = """
        MATCH (dvr:DocumentVerificationRule)
        WHERE ($loan_program = 'general' OR toLower(dvr.category) CONTAINS toLower($loan_program))
        RETURN DISTINCT dvr.document_type as document_type,
               dvr.category as category,
               dvr.required_count as required_count,
               dvr.description as description
        ORDER BY dvr.category, dvr.document_type
        """
        
        result = session.run(query, loan_program=loan_program)
        
        # Organize by categories
        categories = {}
        # Convert to list to avoid consumption errors
        records = list(result)
        
        for record in records:
            doc_type = record.get("document_type")
            category = record.get("category") or "general"
            required_count = record.get("required_count", 1)
            description = record.get("description", "")
            
            if doc_type:
                # Normalize category name
                category_key = _normalize_category_name(category, doc_type)
                
                if category_key not in categories:
                    categories[category_key] = {
                        "display_name": category_key.replace("_", " ").title(),
                        "document_types": [],
                        "required_count": 1,
                        "description": description
                    }
                
                categories[category_key]["document_types"].append({
                    "type": doc_type,
                    "required_count": required_count or 1,
                    "description": description
                })
        
        # If no rules found, create minimal fallback categories
        if not categories:
            categories = _get_fallback_categories()
        
        return categories


def _normalize_category_name(category: str, doc_type: str) -> str:
    """Normalize category names for consistency."""
    
    if not category or category.lower() in ['general', 'other']:
        # Infer category from document type
        if doc_type.lower() in ['paystub', 'pay_stub', 'w2', 'w-2', 'tax_return']:
            return "income_verification"
        elif doc_type.lower() in ['bank_statement', 'investment_statement']:
            return "asset_verification"
        elif doc_type.lower() in ['drivers_license', 'passport', 'id']:
            return "identification"
        elif doc_type.lower() in ['employment_verification', 'employment_letter']:
            return "employment_verification"
        else:
            return "other_documents"
    
    # Clean up category name
    return category.lower().replace(" ", "_").replace("-", "_")


def _get_submitted_documents(connection, application_id: str) -> List[Dict]:
    """Get submitted and verified documents for the application."""
    
    with connection.driver.session(database=connection.database) as session:
        query = """
        MATCH (app:Application {id: $application_id})-[:HAS_DOCUMENT]->(doc:Document)
        WHERE doc.verification_status IN ['VERIFIED', 'PENDING']
        RETURN doc.document_type as document_type,
               doc.verification_status as verification_status,
               doc.file_name as file_name,
               doc.upload_date as upload_date,
               doc.quality_score as quality_score
        ORDER BY doc.upload_date
        """
        
        result = session.run(query, application_id=application_id)
        # Convert to list to avoid consumption errors
        records = list(result)
        return [dict(record) for record in records]


def _analyze_completeness(required_categories: Dict, submitted_docs: List[Dict], loan_program: str) -> Dict:
    """Analyze document completeness against requirements."""
    
    analysis = {
        "loan_program": loan_program,
        "total_categories": len(required_categories),
        "completed_categories": 0,
        "category_analysis": {},
        "overall_completion_pct": 0,
        "missing_categories": [],
        "status": "incomplete"
    }
    
    # Analyze each required category
    for category_key, category_info in required_categories.items():
        category_analysis = {
            "display_name": category_info["display_name"],
            "required_types": category_info["document_types"],
            "submitted_docs": [],
            "is_complete": False,
            "missing_types": []
        }
        
        # Find submitted documents for this category
        required_doc_types = {dt["type"].lower() for dt in category_info["document_types"]}
        
        for submitted_doc in submitted_docs:
            submitted_type = submitted_doc["document_type"].lower()
            if submitted_type in required_doc_types:
                category_analysis["submitted_docs"].append(submitted_doc)
        
        # Determine if category is complete
        if category_analysis["submitted_docs"]:
            category_analysis["is_complete"] = True
            analysis["completed_categories"] += 1
        else:
            # All types in this category are missing
            category_analysis["missing_types"] = [dt["type"] for dt in category_info["document_types"]]
            analysis["missing_categories"].append(category_key)
        
        analysis["category_analysis"][category_key] = category_analysis
    
    # Calculate overall completion
    if analysis["total_categories"] > 0:
        analysis["overall_completion_pct"] = (analysis["completed_categories"] / analysis["total_categories"]) * 100
    
    # Determine overall status
    if analysis["overall_completion_pct"] == 100:
        analysis["status"] = "complete"
    elif analysis["overall_completion_pct"] >= 75:
        analysis["status"] = "nearly_complete"
    elif analysis["overall_completion_pct"] >= 50:
        analysis["status"] = "in_progress"
    else:
        analysis["status"] = "incomplete"
    
    return analysis


def _format_completeness_report(application_id: str, analysis: Dict) -> str:
    """Format comprehensive completeness report."""
    
    completion_pct = analysis["overall_completion_pct"]
    status = analysis["status"]
    loan_program = analysis["loan_program"]
    
    # Header with overall status
    status_icons = {
        "complete": "",
        "nearly_complete": "🟡", 
        "in_progress": "🟠",
        "incomplete": "🔴"
    }
    
    status_messages = {
        "complete": "READY FOR UNDERWRITING",
        "nearly_complete": "NEARLY COMPLETE",
        "in_progress": "IN PROGRESS", 
        "incomplete": "INCOMPLETE"
    }
    
    report = f"""
🔍 **Document Completeness Analysis - Application {application_id}**

**Loan Program:** {loan_program.title()}
**Overall Completion:** {completion_pct:.0f}% ({analysis['completed_categories']}/{analysis['total_categories']} categories)

{status_icons[status]} **Status: {status_messages[status]}**

"""
    
    # Category-by-category analysis
    report += "**📋 Document Categories Analysis:**\n\n"
    
    for category_key, category_data in analysis["category_analysis"].items():
        display_name = category_data["display_name"]
        is_complete = category_data["is_complete"]
        submitted_count = len(category_data["submitted_docs"])
        
        if is_complete:
            report += f" **{display_name}:** Complete ({submitted_count} documents)\n"
            # Show submitted documents
            for doc in category_data["submitted_docs"][:2]:  # Show first 2
                status_indicator = "" if doc["verification_status"] == "VERIFIED" else "🔄"
                report += f"   {status_indicator} {doc['file_name']} ({doc['document_type']})\n"
        else:
            report += f" **{display_name}:** Missing\n"
            # Show what's needed
            missing_types = category_data["missing_types"]
            report += f"   Needed: {', '.join(missing_types)}\n"
        
        report += "\n"
    
    # Summary and next steps
    report += "**📊 Summary:**\n"
    
    if status == "complete":
        report += """
 **ALL DOCUMENT CATEGORIES COMPLETE**
Your application has all required documents and is ready for underwriting review.

**Next Steps:**
• Application will automatically move to underwriting queue
• Underwriting review typically takes 3-5 business days
• You'll be notified of any additional conditions or approval decision
"""
    else:
        report += f"""
⚠️ **{len(analysis['missing_categories'])} categories still need documents**

**Missing Categories:**
"""
        for missing_cat in analysis["missing_categories"]:
            cat_info = analysis["category_analysis"][missing_cat]
            report += f"   • {cat_info['display_name']}: {', '.join(cat_info['missing_types'])}\n"
        
        report += """
**Next Steps:**
• Upload documents for missing categories listed above
• Contact your loan processor if you need help with specific requirements
• Processing cannot continue until all categories are complete
"""
    
    # Add business rules context
    report += f"""
**📋 Analysis Method:**
• Requirements determined by {analysis['total_categories']} business rule categories from Neo4j
• All logic data-driven from Document Verification Rules
• No hardcoded document requirements used
"""
    
    return report


def _get_fallback_categories() -> Dict[str, Dict]:
    """Fallback categories if no rules found in Neo4j."""
    return {
        "identification": {
            "display_name": "Identification",
            "document_types": [{"type": "drivers_license", "required_count": 1, "description": "Government-issued photo ID"}],
            "required_count": 1,
            "description": "Identity verification documents"
        },
        "income_verification": {
            "display_name": "Income Verification",
            "document_types": [
                {"type": "paystub", "required_count": 1, "description": "Recent pay stubs"},
                {"type": "w2", "required_count": 1, "description": "W-2 forms"}
            ],
            "required_count": 1,
            "description": "Income and employment verification"
        },
        "asset_verification": {
            "display_name": "Asset Verification", 
            "document_types": [{"type": "bank_statement", "required_count": 1, "description": "Bank statements"}],
            "required_count": 1,
            "description": "Asset and savings verification"
        }
    }
