"""
DocumentAgent Tools

All tools for document processing, extraction, validation, and knowledge graph population.
Each tool is data-driven using Neo4j business rules - no hardcoded logic.
"""

from .extract_document_data import extract_document_data
from .request_required_documents import request_required_documents
from .process_uploaded_document import process_uploaded_document
from .get_document_status import get_document_status
from .verify_document_completeness import verify_document_completeness
from .validate_identity_document import validate_identity_document

# Import shared application data tools for accessing stored applications
try:
    from agents.shared.application_data_tools import (
        get_stored_application_data,
        list_stored_applications,
        find_application_by_name
    )
except ImportError:
    from agents.shared.application_data_tools import (
        get_stored_application_data,
        list_stored_applications,
        find_application_by_name
    )


def get_all_document_agent_tools():
    """
    Get all DocumentAgent tools.
    
    Returns:
        List of LangChain tools for DocumentAgent
    """
    return [
        extract_document_data,
        request_required_documents,
        process_uploaded_document,
        get_document_status,
        verify_document_completeness,
        validate_identity_document,
        
        # Shared application data tools for accessing stored applications
        get_stored_application_data,
        list_stored_applications,
        find_application_by_name
    ]


__all__ = [
    "extract_document_data",
    "request_required_documents",
    "process_uploaded_document", 
    "get_document_status",
    "verify_document_completeness",
    "validate_identity_document",
    "get_all_document_agent_tools"
]
