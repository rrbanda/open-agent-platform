"""
Agent Database Runtime Utilities

Minimal database utilities for mortgage processing agents to connect to and 
interact with the deployed mortgage database system.

Components:
- neo4j_connection: Connect to deployed mortgage-db system  
- application_storage: Store and retrieve agent-generated application data

Architecture:
- Database setup/loading: Handled by separate mortgage-db repository
- Agent runtime operations: Handled by this minimal utility package
- Business rules/domain data: Queried from deployed mortgage-db system
"""

from .neo4j_connection import Neo4jConnection, get_neo4j_connection, initialize_connection
from .application_storage import (
    MortgageApplicationData,
    store_application_data,
    get_application_data,
    list_applications,
    update_application_status
)

__all__ = [
    # Connection utilities
    "Neo4jConnection",
    "get_neo4j_connection", 
    "initialize_connection",
    
    # Agent storage operations
    "MortgageApplicationData",
    "store_application_data",
    "get_application_data", 
    "list_applications",
    "update_application_status"
]
