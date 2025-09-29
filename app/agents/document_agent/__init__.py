"""
DocumentAgent Package

Production-ready document processing agent for mortgage applications.
Handles complete document workflow using Neo4j Document Verification Rules.

Features:
- Document collection and requirement analysis
- Upload processing and validation
- Content extraction with business rules
- Status tracking and completeness analysis
- Data-driven workflow management
"""

from .agent import create_document_agent

__all__ = ["create_document_agent"]
