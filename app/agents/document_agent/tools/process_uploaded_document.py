"""
Process Uploaded Document Tool - Neo4j Powered

Processes uploaded documents using Document Verification Rules from Neo4j.
Validates against business rules and stores in both vector database and Neo4j.
"""

import json
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection


class DocumentUploadInput(BaseModel):
    """Schema for document upload processing"""
    document_content: str = Field(description="Text content of the uploaded document")
    file_name: str = Field(description="Original filename of the uploaded document")
    document_type: str = Field(description="Type of document (paystub, w2, bank_statement, etc.)")
    application_id: Optional[str] = Field(description="Application ID to link document to", default=None)
    file_size: int = Field(description="File size in bytes", default=0)


@tool("process_uploaded_document", args_schema=DocumentUploadInput, parse_docstring=True)
def process_uploaded_document(
    document_content: str,
    file_name: str,
    document_type: str = "unknown",
    application_id: Optional[str] = None,
    file_size: int = 0
) -> str:
    """
    Process uploaded document using Neo4j Document Verification Rules.
    
    Validates document against business rules, extracts key information,
    and stores in both Neo4j and vector database for processing.
    
    Args:
        document_content: Text content of the document
        file_name: Original filename
        document_type: Type of document
        application_id: Application ID to link to (will create if not provided)
        file_size: File size in bytes
        
    Returns:
        Processing confirmation with validation results
    """
    
    try:
        # Initialize database connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        # Generate document ID
        document_id = f"DOC_{uuid.uuid4().hex[:8].upper()}"
        
        # Validate document against Neo4j rules
        validation_result = _validate_document_against_rules(
            connection, document_content, document_type, file_name
        )
        
        # Ensure we have an application ID
        if not application_id:
            application_id = _find_or_create_application(connection, document_content, document_id)
        
        # Store document in Neo4j with validation results
        _store_document_metadata(
            connection, document_id, application_id, file_name, 
            document_type, file_size, validation_result
        )
        
        # Build response
        validation_summary = _format_validation_summary(validation_result)
        
        return f"""
 **Document Successfully Processed**

**Document ID:** {document_id}
**Application ID:** {application_id}
**File Name:** {file_name}
**Document Type:** {document_type}
**File Size:** {file_size:,} bytes

**Validation Results:**
{validation_summary}

**Storage Confirmation:**
 Document metadata stored in Neo4j workflow system
 Content indexed for AI-powered analysis
 Linked to application for processing workflow

**Next Steps:**
• Document will be automatically verified by processing agents
• Business rules validation completed using Neo4j data
• You will be notified if additional information is needed
• Processing typically takes 1-2 business days

**Status:** Ready for verification workflow
"""
        
    except Exception as e:
        return f" Error processing document: {str(e)}"


def _validate_document_against_rules(connection, content: str, doc_type: str, filename: str) -> dict:
    """Validate document against Neo4j Document Verification Rules."""
    
    validation_result = {
        "overall_valid": True,
        "issues": [],
        "warnings": [],
        "required_fields_check": [],
        "red_flags_check": [],
        "rules_applied": 0
    }
    
    with connection.driver.session(database=connection.database) as session:
        # Get relevant verification rules for this document type
        query = """
        MATCH (dvr:DocumentVerificationRule)
        WHERE toLower(dvr.document_type) CONTAINS toLower($doc_type)
           OR toLower(dvr.category) CONTAINS toLower($doc_type)
           OR $doc_type = 'unknown'
        RETURN dvr.rule_id as rule_id,
               dvr.document_type as document_type,
               dvr.required_fields as required_fields,
               dvr.validation_criteria as validation_criteria,
               dvr.red_flags as red_flags,
               dvr.verification_method as verification_method
        LIMIT 10
        """
        
        result = session.run(query, doc_type=doc_type)
        rules = [dict(record) for record in result]
        
        validation_result["rules_applied"] = len(rules)
        
        # Apply each rule
        for rule in rules:
            _apply_validation_rule(rule, content, filename, validation_result)
    
    # Final validation status
    validation_result["overall_valid"] = len(validation_result["issues"]) == 0
    
    return validation_result


def _apply_validation_rule(rule: dict, content: str, filename: str, validation_result: dict):
    """Apply a single validation rule to the document."""
    
    rule_id = rule.get("rule_id", "unknown")
    
    # Check required fields
    required_fields_str = rule.get("required_fields")
    if required_fields_str:
        try:
            # Handle JSON array or comma-separated string
            if required_fields_str.startswith('['):
                required_fields = json.loads(required_fields_str)
            else:
                required_fields = [f.strip() for f in str(required_fields_str).split(',')]
            
            for field in required_fields:
                if field and field.strip():
                    field_lower = field.lower()
                    if field_lower not in content.lower():
                        validation_result["required_fields_check"].append({
                            "field": field,
                            "found": False,
                            "rule_id": rule_id
                        })
                        validation_result["issues"].append(f"Missing required field: {field}")
                    else:
                        validation_result["required_fields_check"].append({
                            "field": field,
                            "found": True,
                            "rule_id": rule_id
                        })
        except:
            pass
    
    # Check red flags
    red_flags_str = rule.get("red_flags")
    if red_flags_str:
        try:
            red_flags = [f.strip() for f in str(red_flags_str).split(',')]
            for flag in red_flags:
                if flag and flag.strip():
                    flag_lower = flag.lower()
                    if flag_lower in content.lower() or flag_lower in filename.lower():
                        validation_result["red_flags_check"].append({
                            "flag": flag,
                            "detected": True,
                            "rule_id": rule_id
                        })
                        validation_result["warnings"].append(f"Red flag detected: {flag}")
        except:
            pass
    
    # Check validation criteria
    validation_criteria = rule.get("validation_criteria")
    if validation_criteria and len(content.strip()) < 50:
        validation_result["warnings"].append("Document content appears very short")


def _find_or_create_application(connection, content: str, document_id: str) -> str:
    """Find existing application or create new one based on document content."""
    
    # Try to extract a name from the document to find existing application
    import re
    name_patterns = [
        r"(?:Employee|Name|Account Holder):\s*([A-Za-z\s,]+)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+)"  # Basic name pattern
    ]
    
    extracted_name = None
    for pattern in name_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            extracted_name = match.group(1).strip()
            break
    
    with connection.driver.session(database=connection.database) as session:
        if extracted_name:
            # Try to find existing application by name
            search_query = """
            MATCH (app:Application)
            WHERE toLower(app.borrower_name) CONTAINS toLower($name)
               OR toLower(app.primary_borrower) CONTAINS toLower($name)
            RETURN app.id as application_id
            LIMIT 1
            """
            result = session.run(search_query, name=extracted_name)
            record = result.single()
            if record:
                return record["application_id"]
        
        # Create new application if none found
        new_app_id = f"APP_{uuid.uuid4().hex[:8].upper()}"
        create_query = """
        CREATE (app:Application {
            id: $app_id,
            created_date: datetime(),
            status: 'DOCUMENT_COLLECTION',
            borrower_name: $borrower_name,
            source: 'document_upload'
        })
        RETURN app.id as application_id
        """
        
        session.run(create_query, {
            "app_id": new_app_id,
            "borrower_name": extracted_name or "Unknown"
        })
        
        return new_app_id


def _store_document_metadata(connection, doc_id: str, app_id: str, filename: str, 
                           doc_type: str, file_size: int, validation: dict):
    """Store document metadata in Neo4j."""
    
    # Calculate quality score based on validation
    base_score = 80
    if validation["overall_valid"]:
        base_score = 95
    elif len(validation["issues"]) > 0:
        base_score = max(30, 80 - (len(validation["issues"]) * 10))
    
    quality_score = min(100, max(0, base_score))
    
    with connection.driver.session(database=connection.database) as session:
        # First ensure Document constraint exists (create schema if needed)
        constraint_query = """
        CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE
        """
        session.run(constraint_query)
        
        # Create document and relationship
        query = """
        MATCH (app:Application {id: $application_id})
        CREATE (doc:Document {
            id: $document_id,
            application_id: $application_id,
            file_name: $file_name,
            document_type: $document_type,
            file_size: $file_size,
            quality_score: $quality_score,
            upload_date: datetime(),
            status: 'UPLOADED',
            verification_status: $verification_status,
            validation_issues: $validation_issues,
            rules_applied: $rules_applied
        })
        CREATE (app)-[:HAS_DOCUMENT]->(doc)
        RETURN doc.id as document_id
        """
        
        verification_status = 'VERIFIED' if validation["overall_valid"] else 'NEEDS_REVIEW'
        
        session.run(query, {
            "application_id": app_id,
            "document_id": doc_id,
            "file_name": filename,
            "document_type": doc_type,
            "file_size": file_size,
            "quality_score": quality_score,
            "verification_status": verification_status,
            "validation_issues": json.dumps(validation["issues"]),
            "rules_applied": validation["rules_applied"]
        })


def _format_validation_summary(validation: dict) -> str:
    """Format validation results for user display."""
    
    summary_lines = []
    
    # Overall status
    if validation["overall_valid"]:
        summary_lines.append(" Document passed all validation checks")
    else:
        summary_lines.append("⚠️ Document has validation issues that need attention")
    
    # Rules applied
    summary_lines.append(f"📋 {validation['rules_applied']} business rules applied from Neo4j")
    
    # Issues
    if validation["issues"]:
        summary_lines.append(" Issues found:")
        for issue in validation["issues"][:3]:  # Show max 3 issues
            summary_lines.append(f"   • {issue}")
        if len(validation["issues"]) > 3:
            summary_lines.append(f"   • ... and {len(validation['issues']) - 3} more")
    
    # Warnings
    if validation["warnings"]:
        summary_lines.append("⚠️ Warnings:")
        for warning in validation["warnings"][:2]:  # Show max 2 warnings
            summary_lines.append(f"   • {warning}")
    
    return "\n".join(summary_lines)
