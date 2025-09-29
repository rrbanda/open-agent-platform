"""
Core Database Module - Essential Neo4j Operations

This module consolidates all essential database operations:
- Neo4j connection management
- Application data storage and retrieval
- Core database utilities used by all agents

Combines the functionality of neo4j_connection.py and application_storage.py
into a single, focused database module.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback if pydantic not available
    class BaseModel:
        def model_dump(self):
            return {}
    def Field(*args, **kwargs):
        return None

from .config import AppConfig

logger = logging.getLogger(__name__)


# ==== CONNECTION MANAGEMENT ====

class Neo4jConnection:
    """
    Neo4j database connection manager with centralized configuration.
    
    Supports both local Neo4j Desktop and production deployments with
    configuration from config.yaml and environment variable overrides.
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        self._driver: Optional[Driver] = None
        self._app_config = config or AppConfig.load()
        self._neo4j_config = self._app_config.neo4j
    
    @property
    def config(self) -> Dict[str, Any]:
        """
        Get Neo4j configuration as dictionary.
        
        Configuration comes from config.yaml with environment variable overrides.
        Supports your local Neo4j Desktop "mortgage" database instance.
        """
        return {
            "uri": self._neo4j_config.uri,
            "username": self._neo4j_config.username, 
            "password": self._neo4j_config.password,
            "database": self._neo4j_config.database,
            "max_connection_lifetime": self._neo4j_config.max_connection_lifetime,
            "max_connection_pool_size": self._neo4j_config.max_connection_pool_size,
            "connection_acquisition_timeout": self._neo4j_config.connection_acquisition_timeout,
            "enable_mcp": self._neo4j_config.enable_mcp
        }
    
    def connect(self) -> bool:
        """
        Establish connection to Neo4j database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        config = self.config
        if not config["password"]:
            logger.error("Neo4j password is required. Set NEO4J_PASSWORD environment variable or configure in config.yaml")
            return False
        
        try:
            self._driver = GraphDatabase.driver(
                config["uri"],
                auth=(config["username"], config["password"]),
                max_connection_lifetime=config["max_connection_lifetime"],
                max_connection_pool_size=config["max_connection_pool_size"],
                connection_acquisition_timeout=config["connection_acquisition_timeout"]
            )
            
            # Verify connectivity
            self._driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {config['uri']} database '{config['database']}'")
            return True
            
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            return False
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable at {config['uri']}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            return False
    
    def disconnect(self):
        """Close the Neo4j connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
    
    @property
    def driver(self) -> Optional[Driver]:
        """Get the Neo4j driver instance."""
        return self._driver
    
    @property 
    def database(self) -> str:
        """Get the configured database name."""
        return self.config["database"]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Neo4j connection.
        
        Returns:
            Dict with health status information
        """
        if not self._driver:
            return {
                "status": "disconnected",
                "message": "No active database connection",
                "connected": False
            }
        
        try:
            # Simple query to test connectivity
            with self._driver.session(database=self.config["database"]) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                
                if test_value == 1:
                    return {
                        "status": "healthy",
                        "message": "Database connection is working properly",
                        "connected": True,
                        "database": self.config["database"],
                        "uri": self.config["uri"]
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Unexpected response from database",
                        "connected": False
                    }
                    
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error", 
                "message": f"Health check failed: {str(e)}",
                "connected": False
            }

    def execute_query(self, query: str, parameters: Optional[Dict] = None) -> Any:
        """
        Execute a Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            Query result
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j database. Call connect() first.")
        
        with self._driver.session(database=self.config["database"]) as session:
            return session.run(query, parameters or {})
    
    def execute_write_transaction(self, transaction_function, *args, **kwargs):
        """
        Execute a write transaction.
        
        Args:
            transaction_function: Function to execute in transaction
            *args, **kwargs: Arguments to pass to transaction function
            
        Returns:
            Transaction result
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j database. Call connect() first.")
        
        with self._driver.session(database=self.config["database"]) as session:
            return session.execute_write(transaction_function, *args, **kwargs)
    
    def execute_read_transaction(self, transaction_function, *args, **kwargs):
        """
        Execute a read transaction.
        
        Args:
            transaction_function: Function to execute in transaction  
            *args, **kwargs: Arguments to pass to transaction function
            
        Returns:
            Transaction result
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j database. Call connect() first.")
        
        with self._driver.session(database=self.config["database"]) as session:
            return session.execute_read(transaction_function, *args, **kwargs)


# Global connection instance
_neo4j_connection: Optional[Neo4jConnection] = None


def get_neo4j_connection() -> Neo4jConnection:
    """
    Get or create a global Neo4j connection instance.
    
    This function provides a singleton pattern for database connections,
    ensuring connection reuse across the application.
    
    Returns:
        Neo4jConnection: Global connection instance
    """
    global _neo4j_connection
    
    if _neo4j_connection is None:
        _neo4j_connection = Neo4jConnection()
    
    return _neo4j_connection


def initialize_connection() -> bool:
    """
    Initialize the global Neo4j connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    connection = get_neo4j_connection()
    return connection.connect()


# ==== APPLICATION DATA MODELS & STORAGE ====

class MortgageApplicationData(BaseModel):
    """
    Structured data model for mortgage applications.
    
    This model represents all the information collected from a mortgage
    application and provides a standardized format for cross-agent access.
    """
    # Application metadata
    application_id: str = Field(..., description="Unique application identifier")
    received_date: str = Field(..., description="Date/time application was received (ISO format)")
    current_status: str = Field(..., description="Current application status")
    
    # Personal Information
    first_name: str = Field(..., description="Applicant's first name")
    last_name: str = Field(..., description="Applicant's last name")
    middle_name: Optional[str] = Field(None, description="Applicant's middle name")
    ssn: str = Field(..., description="Social Security Number")
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    phone: str = Field(..., description="Phone number")
    email: str = Field(..., description="Email address")
    marital_status: Optional[str] = Field(None, description="Marital status")
    
    # Address Information
    current_street: str = Field(..., description="Current street address")
    current_city: str = Field(..., description="Current city")
    current_state: str = Field(..., description="Current state")
    current_zip: str = Field(..., description="Current ZIP code")
    years_at_address: Optional[float] = Field(None, description="Years at current address")
    
    # Employment Information
    employer_name: str = Field(..., description="Current employer name")
    job_title: str = Field(..., description="Current job title")
    years_employed: Optional[float] = Field(None, description="Years with current employer")
    monthly_income: float = Field(..., description="Monthly gross income")
    annual_income: Optional[float] = Field(None, description="Annual gross income")
    
    # Loan Information
    loan_purpose: str = Field(..., description="Purpose of loan (purchase, refinance, etc.)")
    requested_amount: float = Field(..., description="Requested loan amount")
    property_address: str = Field(..., description="Property address")
    property_city: str = Field(..., description="Property city")
    property_state: str = Field(..., description="Property state")
    property_zip: str = Field(..., description="Property ZIP code")
    property_value: Optional[float] = Field(None, description="Estimated property value")
    down_payment: Optional[float] = Field(None, description="Down payment amount")
    
    # Financial Information
    checking_balance: Optional[float] = Field(None, description="Checking account balance")
    savings_balance: Optional[float] = Field(None, description="Savings account balance")
    other_assets: Optional[float] = Field(None, description="Other assets value")
    monthly_debt_payments: Optional[float] = Field(None, description="Total monthly debt payments")
    credit_score: Optional[int] = Field(None, description="Credit score")
    
    # Additional Information
    first_time_buyer: Optional[bool] = Field(None, description="Is first-time home buyer")
    
    # Processing Information
    workflow_notes: Optional[str] = Field(None, description="Workflow processing notes")


def store_application_data(app_data: MortgageApplicationData) -> Tuple[bool, str]:
    """
    Store mortgage application data in Neo4j database.
    
    Creates a MortgageApplication node with all application information
    and makes it available for other agents in the workflow.
    
    Args:
        app_data: MortgageApplicationData instance with application information
        
    Returns:
        Tuple of (success: bool, result_message: str)
    """
    try:
        # Initialize connection if needed
        connection = get_neo4j_connection()
        if not connection.driver:
            if not initialize_connection():
                return False, "Failed to connect to Neo4j database"
        
        # Convert Pydantic model to dict for Neo4j storage
        data_dict = app_data.model_dump()
        
        # Create the application node in Neo4j
        query = """
        CREATE (app:MortgageApplication)
        SET app += $app_data
        SET app.created_timestamp = datetime()
        SET app.updated_timestamp = datetime()
        RETURN app.application_id as stored_id
        """
        
        result = connection.execute_query(query, {"app_data": data_dict})
        stored_record = result.single()
        
        if stored_record:
            stored_id = stored_record["stored_id"]
            logger.info(f"Successfully stored mortgage application: {stored_id}")
            return True, f"Application {stored_id} stored successfully in mortgage database"
        else:
            return False, "Failed to store application - no record created"
            
    except Exception as e:
        logger.error(f"Error storing application data: {e}")
        return False, f"Error storing application: {str(e)}"


def get_application_data(application_id: str) -> Tuple[bool, Any]:
    """
    Retrieve mortgage application data from Neo4j database.
    
    Args:
        application_id: The application ID to retrieve
        
    Returns:
        Tuple of (success: bool, application_data: dict or error_message: str)
    """
    try:
        # Initialize connection if needed
        connection = get_neo4j_connection()
        if not connection.driver:
            if not initialize_connection():
                return False, "Failed to connect to Neo4j database"
        
        # Query for the application
        query = """
        MATCH (app:MortgageApplication {application_id: $app_id})
        RETURN app
        """
        
        result = connection.execute_query(query, {"app_id": application_id})
        record = result.single()
        
        if record:
            app_data = dict(record["app"])
            logger.info(f"Retrieved mortgage application: {application_id}")
            return True, app_data
        else:
            return False, f"Application {application_id} not found in database"
            
    except Exception as e:
        logger.error(f"Error retrieving application data: {e}")
        return False, f"Error retrieving application: {str(e)}"


def update_application_status(application_id: str, new_status: str, notes: str = "") -> Tuple[bool, str]:
    """
    Update the status of a mortgage application.
    
    Args:
        application_id: The application ID to update
        new_status: New status value
        notes: Optional notes about the status change
        
    Returns:
        Tuple of (success: bool, result_message: str)
    """
    try:
        # Initialize connection if needed
        connection = get_neo4j_connection()
        if not connection.driver:
            if not initialize_connection():
                return False, "Failed to connect to Neo4j database"
        
        # Update the application status
        query = """
        MATCH (app:MortgageApplication {application_id: $app_id})
        SET app.current_status = $new_status,
            app.updated_timestamp = datetime()
        SET app.workflow_notes = CASE 
            WHEN app.workflow_notes IS NULL THEN $notes
            ELSE app.workflow_notes + '; ' + $notes
        END
        RETURN app.application_id as updated_id, app.current_status as status
        """
        
        result = connection.execute_query(query, {
            "app_id": application_id,
            "new_status": new_status,
            "notes": notes
        })
        record = result.single()
        
        if record:
            updated_id = record["updated_id"]
            status = record["status"]
            logger.info(f"Updated application {updated_id} status to: {status}")
            return True, f"Application {updated_id} status updated to: {status}"
        else:
            return False, f"Application {application_id} not found for status update"
            
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        return False, f"Error updating application: {str(e)}"


def list_applications(limit: int = 10) -> Tuple[bool, Any]:
    """
    List recent mortgage applications.
    
    Args:
        limit: Maximum number of applications to return
        
    Returns:
        Tuple of (success: bool, applications: list or error_message: str)
    """
    try:
        # Initialize connection if needed
        connection = get_neo4j_connection()
        if not connection.driver:
            if not initialize_connection():
                return False, "Failed to connect to Neo4j database"
        
        # Query for recent applications
        query = """
        MATCH (app:MortgageApplication)
        RETURN app.application_id as application_id,
               app.first_name as first_name,
               app.last_name as last_name,
               app.current_status as status,
               app.received_date as received_date
        ORDER BY app.created_timestamp DESC
        LIMIT $limit
        """
        
        result = connection.execute_query(query, {"limit": limit})
        applications = []
        
        # Convert result to list immediately to avoid consumption errors
        records = list(result)
        
        for record in records:
            applications.append({
                "application_id": record["application_id"],
                "first_name": record["first_name"],
                "last_name": record["last_name"],
                "status": record["status"],
                "received_date": record["received_date"]
            })
        
        logger.info(f"Retrieved {len(applications)} mortgage applications")
        return True, applications
        
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        return False, f"Error listing applications: {str(e)}"
