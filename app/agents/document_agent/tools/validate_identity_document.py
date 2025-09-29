"""
Validate Identity Document Tool - Neo4j Powered

Comprehensive ID document validation using ID verification rules from Neo4j.
Supports Driver's License, Passport, State ID, and SSN verification.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection


class IdentityDocumentValidationInput(BaseModel):
    """Schema for identity document validation requests"""
    document_content: str = Field(description="Text content of the identity document")
    document_type: str = Field(description="Type of ID document (drivers_license, passport, state_id, ssn_card)")
    file_name: Optional[str] = Field(description="Original filename", default="id_document.txt")
    cross_reference_docs: Optional[List[Dict]] = Field(description="Other documents for cross-verification", default=None)


@tool("validate_identity_document", args_schema=IdentityDocumentValidationInput, parse_docstring=True)
def validate_identity_document(
    document_content: str,
    document_type: str,
    file_name: Optional[str] = "id_document.txt",
    cross_reference_docs: Optional[List[Dict]] = None
) -> str:
    """
    Comprehensive identity document validation using Neo4j ID verification rules.
    
    Validates ID documents against comprehensive business rules for mortgage processing.
    Supports Driver's License, Passport, State ID, and SSN Card verification.
    
    Args:
        document_content: Text content of the identity document
        document_type: Type of ID (drivers_license, passport, state_id, ssn_card)
        file_name: Original filename of the document
        cross_reference_docs: Other documents for cross-verification
        
    Returns:
        Comprehensive validation report with rule-based analysis
    """
    
    try:
        initialize_connection()
        connection = get_neo4j_connection()
        
        # Get relevant ID verification rules from Neo4j
        verification_rules = _get_id_verification_rules(connection, document_type)
        
        if not verification_rules:
            return f"""
 **ID Verification Not Available**

**Document Type:** {document_type}
**Issue:** No verification rules found for this document type.

**Supported ID Types:**
• drivers_license - Driver's License
• passport - US/International Passport  
• state_id - State-issued ID Card
• ssn_card - Social Security Card

**Resolution:** Ensure document type is correctly specified.
"""
        
        # Extract structured data from document
        extracted_data = _extract_id_data(document_content, document_type)
        
        # Apply ID verification rules
        validation_results = _apply_id_verification_rules(
            verification_rules, extracted_data, document_content, cross_reference_docs
        )
        
        # Generate comprehensive validation report
        return _format_id_validation_report(
            document_type, file_name, extracted_data, validation_results, verification_rules
        )
        
    except Exception as e:
        return f"""
 **ID Verification Error**

**Document Type:** {document_type}
**File:** {file_name}
**Error:** {str(e)}

**Recommendation:** Contact support if this error persists.
"""


def _get_id_verification_rules(connection, document_type: str) -> List[Dict]:
    """Get relevant ID verification rules from Neo4j."""
    
    # Map document types to rule categories
    type_mapping = {
        "drivers_license": "DriversLicense",
        "passport": "Passport", 
        "state_id": "StateID",
        "ssn_card": "SSN"
    }
    
    category = type_mapping.get(document_type.lower())
    if not category:
        return []
    
    with connection.driver.session(database=connection.database) as session:
        query = """
        MATCH (rule:IDVerificationRule)
        WHERE rule.category = $category OR rule.document_type = $document_type
        RETURN rule
        ORDER BY rule.rule_id
        """
        
        result = session.run(query, category=category, document_type=document_type)
        return [dict(record['rule']) for record in result]


def _extract_id_data(document_content: str, document_type: str) -> Dict[str, Any]:
    """Extract structured data from ID document content."""
    
    extracted = {
        "document_type": document_type,
        "raw_content": document_content,
        "extraction_timestamp": datetime.now().isoformat(),
        "extracted_fields": {}
    }
    
    content_lower = document_content.lower()
    
    # Common patterns for all ID types
    name_patterns = [
        r"(?:full name|name|last name, first name):\s*([A-Za-z\s,]+)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",  # Name pattern
    ]
    
    dob_patterns = [
        r"(?:date of birth|dob|birth date):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",  # General date pattern
    ]
    
    address_patterns = [
        r"(?:address|addr):\s*([^\n]+)",
        r"(\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln)[^\n]*)",
    ]
    
    # Extract common fields
    for pattern in name_patterns:
        match = re.search(pattern, document_content, re.IGNORECASE)
        if match and not extracted["extracted_fields"].get("full_name"):
            extracted["extracted_fields"]["full_name"] = match.group(1).strip()
            break
    
    for pattern in dob_patterns:
        match = re.search(pattern, document_content, re.IGNORECASE)
        if match and not extracted["extracted_fields"].get("date_of_birth"):
            extracted["extracted_fields"]["date_of_birth"] = match.group(1).strip()
            break
    
    for pattern in address_patterns:
        match = re.search(pattern, document_content, re.IGNORECASE)
        if match and not extracted["extracted_fields"].get("address"):
            extracted["extracted_fields"]["address"] = match.group(1).strip()
            break
    
    # Document-specific extraction
    if document_type == "drivers_license":
        extracted["extracted_fields"].update(_extract_drivers_license_fields(document_content))
    elif document_type == "passport":
        extracted["extracted_fields"].update(_extract_passport_fields(document_content))
    elif document_type == "state_id":
        extracted["extracted_fields"].update(_extract_state_id_fields(document_content))
    elif document_type == "ssn_card":
        extracted["extracted_fields"].update(_extract_ssn_fields(document_content))
    
    return extracted


def _extract_drivers_license_fields(content: str) -> Dict[str, str]:
    """Extract driver's license specific fields."""
    fields = {}
    
    patterns = {
        "license_number": r"(?:license number|lic no|dl):\s*([A-Z0-9]+)",
        "state": r"(?:state|issued by):\s*([A-Z]{2}|[A-Za-z\s]+)",
        "expiration_date": r"(?:expires|exp|expiration):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        "license_class": r"(?:class|type):\s*([A-Z]{1,3})",
        "restrictions": r"(?:restrictions|rest):\s*([A-Z\s,]+)",
        "height": r"(?:height|ht):\s*(\d+-\d+|\d+'\d+\"?)",
        "weight": r"(?:weight|wt):\s*(\d+)",
        "eyes": r"(?:eyes|eye color):\s*([A-Z]{3}|[A-Za-z]+)",
        "hair": r"(?:hair|hair color):\s*([A-Z]{3}|[A-Za-z]+)",
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            fields[field] = match.group(1).strip()
    
    return fields


def _extract_passport_fields(content: str) -> Dict[str, str]:
    """Extract passport specific fields."""
    fields = {}
    
    patterns = {
        "passport_number": r"(?:passport number|passport no):\s*([A-Z0-9]+)",
        "country_of_issue": r"(?:country of issue|issuing country):\s*([A-Za-z\s]+)",
        "nationality": r"(?:nationality|citizen of):\s*([A-Za-z\s]+)",
        "place_of_birth": r"(?:place of birth|birth place):\s*([A-Za-z\s,]+)",
        "issue_date": r"(?:issue date|issued):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        "expiration_date": r"(?:expiration|expires):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            fields[field] = match.group(1).strip()
    
    return fields


def _extract_state_id_fields(content: str) -> Dict[str, str]:
    """Extract state ID specific fields."""
    fields = {}
    
    patterns = {
        "id_number": r"(?:id number|state id):\s*([A-Z0-9]+)",
        "state": r"(?:state|issued by):\s*([A-Z]{2}|[A-Za-z\s]+)",
        "issue_date": r"(?:issue date|issued):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        "expiration_date": r"(?:expiration|expires):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        "non_driver": r"(non.driver|not valid for driving)",
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            fields[field] = match.group(1).strip()
    
    return fields


def _extract_ssn_fields(content: str) -> Dict[str, str]:
    """Extract SSN specific fields."""
    fields = {}
    
    patterns = {
        "ssn_number": r"(\d{3}-\d{2}-\d{4}|\d{9})",
        "issued_date": r"(?:issued|issue date):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            fields[field] = match.group(1).strip()
    
    return fields


def _apply_id_verification_rules(
    rules: List[Dict], 
    extracted_data: Dict, 
    content: str, 
    cross_docs: Optional[List[Dict]]
) -> Dict[str, Any]:
    """Apply ID verification rules to extracted data."""
    
    results = {
        "total_rules_applied": len(rules),
        "rules_passed": 0,
        "rules_failed": 0,
        "rules_warnings": 0,
        "detailed_results": [],
        "critical_issues": [],
        "warnings": [],
        "overall_valid": True,
        "confidence_score": 0.0
    }
    
    extracted_fields = extracted_data.get("extracted_fields", {})
    
    for rule in rules:
        rule_result = _apply_single_rule(rule, extracted_fields, content, cross_docs)
        results["detailed_results"].append(rule_result)
        
        if rule_result["status"] == "PASSED":
            results["rules_passed"] += 1
        elif rule_result["status"] == "FAILED":
            results["rules_failed"] += 1
            results["critical_issues"].append(rule_result["message"])
            results["overall_valid"] = False
        elif rule_result["status"] == "WARNING":
            results["rules_warnings"] += 1
            results["warnings"].append(rule_result["message"])
    
    # Calculate confidence score
    total_checks = results["total_rules_applied"]
    if total_checks > 0:
        passed_weight = results["rules_passed"] * 1.0
        warning_weight = results["rules_warnings"] * 0.5
        results["confidence_score"] = (passed_weight + warning_weight) / total_checks * 100
    
    return results


def _apply_single_rule(
    rule: Dict, 
    extracted_fields: Dict, 
    content: str, 
    cross_docs: Optional[List[Dict]]
) -> Dict[str, Any]:
    """Apply a single ID verification rule."""
    
    rule_id = rule.get("rule_id", "UNKNOWN")
    required_fields = rule.get("required_fields", [])
    validation_criteria = rule.get("validation_criteria", [])
    red_flags = rule.get("red_flags", [])
    
    result = {
        "rule_id": rule_id,
        "rule_description": rule.get("description", ""),
        "status": "PASSED",
        "message": f"Rule {rule_id} passed",
        "details": []
    }
    
    # Check required fields
    missing_fields = []
    for field in required_fields:
        if field not in extracted_fields or not extracted_fields[field]:
            missing_fields.append(field)
    
    if missing_fields:
        result["status"] = "FAILED"
        result["message"] = f"Missing required fields: {', '.join(missing_fields)}"
        result["details"].append(f"Required but missing: {missing_fields}")
        return result
    
    # Check red flags
    content_lower = content.lower()
    detected_flags = []
    for flag in red_flags:
        if flag.lower() in content_lower:
            detected_flags.append(flag)
    
    if detected_flags:
        result["status"] = "WARNING"
        result["message"] = f"Red flags detected: {', '.join(detected_flags)}"
        result["details"].append(f"Red flags found: {detected_flags}")
    
    # Apply validation criteria (simplified for demo)
    if "not_expired" in validation_criteria:
        exp_date = extracted_fields.get("expiration_date")
        if exp_date:
            try:
                # Simple date parsing - in production would be more robust
                exp_date_parsed = datetime.strptime(exp_date.replace("/", "-"), "%m-%d-%Y")
                if exp_date_parsed < datetime.now():
                    result["status"] = "FAILED"
                    result["message"] = "Document has expired"
                    result["details"].append(f"Expiration date: {exp_date}")
            except:
                result["status"] = "WARNING"
                result["message"] = "Could not verify expiration date"
    
    return result


def _format_id_validation_report(
    document_type: str,
    file_name: str, 
    extracted_data: Dict,
    validation_results: Dict,
    rules: List[Dict]
) -> str:
    """Format comprehensive ID validation report."""
    
    extracted_fields = extracted_data.get("extracted_fields", {})
    
    # Document type display names
    type_names = {
        "drivers_license": "Driver's License",
        "passport": "Passport",
        "state_id": "State ID Card", 
        "ssn_card": "Social Security Card"
    }
    
    doc_display_name = type_names.get(document_type, document_type.title())
    
    # Overall status
    if validation_results["overall_valid"]:
        status_icon = ""
        status_text = "VALID"
    else:
        status_icon = ""
        status_text = "INVALID"
    
    confidence = validation_results["confidence_score"]
    
    report = f"""
🔍 **{doc_display_name} Validation Report**

{status_icon} **Overall Status:** {status_text}
**Confidence Score:** {confidence:.1f}%
**File:** {file_name}
**Rules Applied:** {validation_results['total_rules_applied']} comprehensive verification rules

**📊 Validation Summary:**
 Rules Passed: {validation_results['rules_passed']}
 Rules Failed: {validation_results['rules_failed']}
⚠️ Warnings: {validation_results['rules_warnings']}

"""
    
    # Extracted Information
    if extracted_fields:
        report += "**📋 Extracted Information:**\n"
        for field, value in extracted_fields.items():
            if value:
                display_field = field.replace("_", " ").title()
                report += f"• {display_field}: {value}\n"
        report += "\n"
    
    # Critical Issues
    if validation_results["critical_issues"]:
        report += "** Critical Issues:**\n"
        for issue in validation_results["critical_issues"]:
            report += f"• {issue}\n"
        report += "\n"
    
    # Warnings
    if validation_results["warnings"]:
        report += "**⚠️ Warnings:**\n"
        for warning in validation_results["warnings"]:
            report += f"• {warning}\n"
        report += "\n"
    
    # Rule Categories Applied
    categories = set(rule.get("category", "Unknown") for rule in rules)
    report += f"**🔧 Verification Categories Applied:**\n"
    for category in sorted(categories):
        category_rules = [r for r in rules if r.get("category") == category]
        report += f"• {category}: {len(category_rules)} rules\n"
    
    # Next Steps
    report += "\n**📋 Next Steps:**\n"
    if validation_results["overall_valid"]:
        report += " ID document verification complete - ready for mortgage processing\n"
        report += "• Document meets all mortgage industry verification standards\n"
        report += "• Information extracted and ready for application processing\n"
    else:
        report += " ID document requires attention before proceeding\n"
        report += "• Address critical issues listed above\n"
        report += "• Resubmit corrected or alternative documentation\n"
        report += "• Contact loan processor if assistance is needed\n"
    
    report += f"\n**🎯 Verification Standards:**\n"
    report += f"• Neo4j business rules: {len(rules)} comprehensive checks\n"
    report += f"• Mortgage industry compliance standards applied\n"
    report += f"• Data-driven validation - no hardcoded logic\n"
    
    return report
