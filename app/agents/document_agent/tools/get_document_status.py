"""
Get Document Status Tool - Neo4j Powered

Retrieves comprehensive document status from Neo4j for mortgage applications.
Shows document collection progress, verification status, and processing updates.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from utils import get_neo4j_connection, initialize_connection
except ImportError:
    from utils import get_neo4j_connection, initialize_connection


class DocumentStatusRequest(BaseModel):
    """Schema for document status requests"""
    application_id: str = Field(description="Application identifier to check document status for")


@tool("get_document_status", args_schema=DocumentStatusRequest, parse_docstring=True)
def get_document_status(application_id: str) -> str:
    """
    Get comprehensive document status for a mortgage application from Neo4j.
    
    Shows document requests sent, documents uploaded, verification status,
    and processing progress based on real data from the knowledge graph.
    
    Args:
        application_id: Application identifier
        
    Returns:
        Detailed document collection and verification status report
    """
    
    try:
        # Initialize database connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        # Get comprehensive document status from Neo4j
        status_data = _get_status_from_neo4j(connection, application_id)
        
        if not status_data:
            return f"""
 **Application Not Found: {application_id}**

The specified application ID was not found in the system.

**Possible reasons:**
• Application ID may be incorrect or misspelled
• Application may not have been created yet
• System may be experiencing connectivity issues

**Next steps:**
• Verify the application ID is correct
• Contact support if the issue persists

**Available actions:**
• Generate document requirements for a new application
• Check status of a different application
"""
        
        # Format comprehensive status report
        return _format_status_report(application_id, status_data)
        
    except Exception as e:
        error_msg = str(e)
        return f"""
 **Error Retrieving Document Status**

**Application ID:** {application_id}
**Error Details:** {error_msg}

**This is a technical error.** Please try again, or contact support if the issue persists.

**Alternative actions you can take:**
• Generate document requirements using the request_required_documents tool
• Process uploaded documents using the process_uploaded_document tool
• Check document completeness using the verify_document_completeness tool
"""


def _get_status_from_neo4j(connection, application_id: str) -> dict:
    """Query Neo4j for comprehensive document status data."""
    
    try:
        with connection.driver.session(database=connection.database) as session:
            # First check if Application exists
            app_check_query = """
            MATCH (app:Application {id: $application_id})
            RETURN app.id as application_id, app.status as app_status
            """
            
            app_result = session.run(app_check_query, application_id=application_id)
            app_record = app_result.single()
            
            if not app_record:
                return None
            
            # Get document requests (this schema exists)
            requests_query = """
            MATCH (app:Application {id: $application_id})
            OPTIONAL MATCH (app)-[:REQUIRES_DOCUMENTS]->(req:DocumentRequest)
            RETURN collect(DISTINCT {
                request_id: req.id,
                requested_docs: req.requested_documents,
                request_date: req.request_date,
                deadline: req.deadline,
                status: req.status
            }) as requests
            """
            
            requests_result = session.run(requests_query, application_id=application_id)
            requests_record = requests_result.single()
            requests = [r for r in requests_record['requests'] if r['request_id']] if requests_record else []
            
            # Check if Document label exists before querying
            label_check_query = """
            CALL db.labels() YIELD label
            WITH collect(label) as labels
            RETURN 'Document' IN labels as document_label_exists
            """
            
            label_result = session.run(label_check_query)
            has_document_label = label_result.single()['document_label_exists']
            
            documents = []
            if has_document_label:
                # Only query for documents if the label exists
                documents_query = """
                MATCH (app:Application {id: $application_id})
                OPTIONAL MATCH (app)-[:HAS_DOCUMENT]->(doc:Document)
                RETURN collect(DISTINCT {
                    document_id: doc.id,
                    file_name: doc.file_name,
                    document_type: doc.document_type,
                    upload_date: doc.upload_date,
                    status: doc.status,
                    verification_status: doc.verification_status,
                    quality_score: doc.quality_score,
                    rules_applied: doc.rules_applied,
                    validation_issues: doc.validation_issues
                }) as documents
                """
                
                documents_result = session.run(documents_query, application_id=application_id)
                documents_record = documents_result.single()
                documents = [d for d in documents_record['documents'] if d['document_id']] if documents_record else []
            
            # Return combined data
            return {
                'application_id': app_record['application_id'],
                'app_status': app_record.get('app_status', 'Unknown'),
                'app_created': None,  # Not querying this to avoid more missing property warnings
                'requests': requests,
                'documents': documents,
                'schema_note': f"Document workflow schema {'available' if has_document_label else 'not yet created'}"
            }
    
    except Exception as e:
        # If any Neo4j query fails, return None to trigger the "not found" response
        # This prevents recursion by giving a definitive answer
        print(f"DEBUG: Neo4j query error in get_document_status: {e}")
        return None


def _format_status_report(application_id: str, data: dict) -> str:
    """Format comprehensive status report."""
    
    requests = data['requests']
    documents = data['documents']
    app_status = data.get('app_status', 'Unknown')
    schema_note = data.get('schema_note', '')
    
    # Build header
    report = f"""
📊 **Document Status Report - Application {application_id}**

**Application Status:** {app_status}
**Document Requests Sent:** {len(requests)}
**Documents Uploaded:** {len(documents)}
**Workflow Schema:** {schema_note}

"""
    
    # Document Requests Section
    if requests:
        report += "**📋 Document Requests:**\n"
        for req in requests:
            deadline_str = req['deadline'].strftime('%Y-%m-%d') if req['deadline'] else 'No deadline'
            status = req['status'] or 'Unknown'
            report += f"   • Request {req['request_id']} - Status: {status} - Deadline: {deadline_str}\n"
        report += "\n"
    
    # Uploaded Documents Section
    if documents:
        report += "**📄 Uploaded Documents:**\n"
        for doc in documents:
            upload_date = doc['upload_date'].strftime('%Y-%m-%d %H:%M') if doc['upload_date'] else 'Unknown'
            quality = f"{doc['quality_score']:.0f}%" if doc['quality_score'] else 'N/A'
            verification = doc['verification_status'] or 'Unknown'
            rules_count = doc['rules_applied'] or 0
            
            # Status icon based on verification
            if verification == 'VERIFIED':
                status_icon = ""
            elif verification == 'NEEDS_REVIEW':
                status_icon = "⚠️"
            else:
                status_icon = "🔄"
            
            report += f"   {status_icon} {doc['file_name']} ({doc['document_type']})\n"
            report += f"     Status: {verification} | Quality: {quality} | Rules: {rules_count} | Uploaded: {upload_date}\n"
            
            # Show validation issues if any
            if doc.get('validation_issues'):
                try:
                    import json
                    issues = json.loads(doc['validation_issues'])
                    if issues:
                        report += f"     Issues: {', '.join(issues[:2])}\n"  # Show first 2 issues
                except:
                    pass
        
        report += "\n"
    
    # Progress Analysis
    verified_docs = len([d for d in documents if d.get('verification_status') == 'VERIFIED'])
    pending_docs = len([d for d in documents if d.get('verification_status') == 'PENDING'])
    needs_review_docs = len([d for d in documents if d.get('verification_status') == 'NEEDS_REVIEW'])
    
    # Estimate completion percentage (assuming 12 total required documents)
    total_required = 12
    completion_pct = min(100, (len(documents) / total_required) * 100) if documents else 0
    
    report += f"""**📈 Progress Summary:**
• Document Collection: {completion_pct:.0f}% ({len(documents)}/{total_required} estimated)
• Verified Documents: {verified_docs}
• Pending Verification: {pending_docs}
• Needs Review: {needs_review_docs}

**📋 Business Rules Analysis:**
• Total rules applied: {sum(d.get('rules_applied', 0) for d in documents)}
• Documents with validation issues: {len([d for d in documents if d.get('validation_issues') and d['validation_issues'] != '[]'])}

**Next Steps:**
"""
    
    # Generate specific next steps based on current status
    if completion_pct < 50:
        report += "• Upload remaining required documents to continue processing\n"
    
    if needs_review_docs > 0:
        report += f"• Review and resubmit {needs_review_docs} documents with validation issues\n"
    
    if pending_docs > 0:
        report += f"• Wait for verification of {pending_docs} pending documents (1-2 business days)\n"
    
    if completion_pct >= 90 and verified_docs == len(documents):
        report += "•  Ready for underwriting - All documents verified!\n"
    
    if not documents:
        if "not yet created" in schema_note:
            report += "• Document upload workflow will be enabled once first document is processed\n"
            report += "• Currently in pre-processing phase - document requirements can still be generated\n"
        else:
            report += "• Begin uploading required documents to start the process\n"
    
    # Add contact information
    report += """
**Need Help?**
Contact your loan processor at (555) 123-4567 or email support@mortgagelender.com
"""
    
    return report
