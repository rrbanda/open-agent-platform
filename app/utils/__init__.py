"""
Mortgage Agent Utils - Clean & Flat Structure

Essential utilities for the mortgage processing agents:

**Core Files:**
- config.py: Configuration + LLM factory functions
- database.py: Neo4j operations + application data
- config.yaml: Settings

**Integrations** (optional):
- integrations/file_uploads.py: LangGraph Studio file upload support

Simple, flat structure with no unnecessary nesting.
"""

# Import LLM functions from config.py (where they're now integrated)
from .config import (
    get_llm,
    get_supervisor_llm, 
    get_agent_llm,
    get_grader_llm,
    AppConfig,
    DocumentType,
    MortgageBaseModel
)

# Import database functions from database.py
from .database import (
    Neo4jConnection,
    get_neo4j_connection,
    initialize_connection,
    MortgageApplicationData,
    store_application_data,
    get_application_data, 
    update_application_status,
    list_applications
)

# Import integrations (optional features)
try:
    from .integrations import (
        extract_message_content_and_files,
        parse_multimodal_content,
        extract_text_from_data_url,
        create_document_processing_input,
        get_uploaded_files_summary
    )
    _integrations_available = True
except ImportError:
    # Graceful fallback if integration dependencies aren't installed
    _integrations_available = False
    extract_message_content_and_files = None
    parse_multimodal_content = None
    extract_text_from_data_url = None
    create_document_processing_input = None
    get_uploaded_files_summary = None

__all__ = [
    # LLM utilities
    "get_llm",
    "get_supervisor_llm", 
    "get_agent_llm",
    "get_grader_llm",
    
    # Configuration
    "AppConfig",
    "DocumentType", 
    "MortgageBaseModel",
    
    # Database utilities
    "Neo4jConnection",
    "get_neo4j_connection",
    "initialize_connection",
    "MortgageApplicationData",
    "store_application_data",
    "get_application_data", 
    "update_application_status",
    "list_applications",
    
    # Integration utilities (if available)
    "extract_message_content_and_files",
    "parse_multimodal_content",
    "extract_text_from_data_url", 
    "create_document_processing_input",
    "get_uploaded_files_summary"
]