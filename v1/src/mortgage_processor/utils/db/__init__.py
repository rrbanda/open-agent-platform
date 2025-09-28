"""
Database Utilities Package

This package provides database connection management and knowledge graph utilities
for the mortgage processing platform.

Components:
- neo4j_connection: Neo4j database connection management
- mcp_client: Model Context Protocol client for Neo4j integration  
- mortgage_knowledge: Mortgage-specific knowledge graph operations
- schema_manager: Knowledge graph schema management

The database utilities are designed to be:
- Reusable across all agents
- Environment-configurable  
- Production-ready with proper error handling
- MCP-enabled for intelligent LLM integration
"""

from .neo4j_connection import Neo4jConnection, get_neo4j_connection, initialize_connection
from .mortgage_data_loader import load_mortgage_data, verify_data_load
from .application_storage import (
    MortgageApplicationData,
    store_application_data,
    get_application_data,
    list_applications,
    update_application_status
)

__all__ = [
    "Neo4jConnection",
    "get_neo4j_connection",
    "initialize_connection", 
    "load_mortgage_data",
    "verify_data_load",
    "MortgageApplicationData",
    "store_application_data",
    "get_application_data",
    "list_applications",
    "update_application_status"
]
