"""
Integrations Package

Optional LangGraph Studio integrations that extend the core mortgage processing system:
- File upload handling for document processing
- Multimodal content parsing

These are optional features that can be disabled if not needed.
"""

from .file_uploads import (
    # Message parsing
    extract_message_content_and_files,
    
    # File processing
    parse_multimodal_content,
    extract_text_from_data_url,
    
    # Helper utilities
    create_document_processing_input,
    get_uploaded_files_summary
)

__all__ = [
    "extract_message_content_and_files",
    "parse_multimodal_content", 
    "extract_text_from_data_url",
    "create_document_processing_input",
    "get_uploaded_files_summary"
]
