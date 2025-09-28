"""
Application Data Storage Module

This module provides data models and storage functions for mortgage applications
in the Neo4j database. It enables cross-agent access to application data for
the mortgage processing workflow.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback if pydantic not available
    class BaseModel:
        def model_dump(self):
            return {}
    def Field(*args, **kwargs):
        return None
from .neo4j_connection import get_neo4j_connection, initialize_connection

logger = logging.getLogger(__name__)


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
    years_at_address: float = Field(..., description="Years at current address")
    
    # Employment Information
    employer_name: str = Field(..., description="Current employer name")
    job_title: str = Field(..., description="Job title/position")
    years_employed: float = Field(..., description="Years with current employer")
    monthly_gross_income: float = Field(..., description="Monthly gross income")
    employment_type: str = Field(..., description="Employment type")
    
    # Loan Information
    loan_purpose: str = Field(..., description="Loan purpose")
    loan_amount: float = Field(..., description="Requested loan amount")
    property_address: str = Field(..., description="Property address")
    property_value: Optional[float] = Field(None, description="Property value")
    property_type: str = Field(..., description="Property type")
    occupancy_type: str = Field(..., description="Occupancy type")
    
    # Financial Information
    credit_score: Optional[int] = Field(None, description="Credit score")
    monthly_debts: Optional[float] = Field(None, description="Monthly debt payments")
    liquid_assets: Optional[float] = Field(None, description="Liquid assets")
    down_payment: Optional[float] = Field(None, description="Down payment amount")
    
    # Special Program Information
    first_time_buyer: bool = Field(default=False, description="First-time buyer status")
    military_service: bool = Field(default=False, description="Military service status")
    rural_property: bool = Field(default=False, description="Rural property status")
    
    # Processing Information
    validation_status: str = Field(..., description="Validation status")
    completion_percentage: float = Field(..., description="Application completion percentage")
    next_agent: Optional[str] = Field(None, description="Next agent in workflow")
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
        CREATE (app:MortgageApplication {
            application_id: $application_id,
            received_date: $received_date,
            current_status: $current_status,
            first_name: $first_name,
            last_name: $last_name,
            middle_name: $middle_name,
            ssn: $ssn,
            date_of_birth: $date_of_birth,
            phone: $phone,
            email: $email,
            marital_status: $marital_status,
            current_street: $current_street,
            current_city: $current_city,
            current_state: $current_state,
            current_zip: $current_zip,
            years_at_address: $years_at_address,
            employer_name: $employer_name,
            job_title: $job_title,
            years_employed: $years_employed,
            monthly_gross_income: $monthly_gross_income,
            employment_type: $employment_type,
            loan_purpose: $loan_purpose,
            loan_amount: $loan_amount,
            property_address: $property_address,
            property_value: $property_value,
            property_type: $property_type,
            occupancy_type: $occupancy_type,
            credit_score: $credit_score,
            monthly_debts: $monthly_debts,
            liquid_assets: $liquid_assets,
            down_payment: $down_payment,
            first_time_buyer: $first_time_buyer,
            military_service: $military_service,
            rural_property: $rural_property,
            validation_status: $validation_status,
            completion_percentage: $completion_percentage,
            next_agent: $next_agent,
            workflow_notes: $workflow_notes,
            created_timestamp: datetime(),
            updated_timestamp: datetime()
        })
        RETURN app.application_id as stored_id
        """
        
        result = connection.execute_query(query, data_dict)
        stored_id = result.single()["stored_id"]
        
        logger.info(f"Successfully stored application {stored_id} in Neo4j")
        
        # Create relationships based on application characteristics
        _create_application_relationships(connection, app_data)
        
        return True, stored_id
        
    except Exception as e:
        error_msg = f"Error storing application data: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def _create_application_relationships(connection, app_data: MortgageApplicationData):
    """
    Create relationships between the application and relevant program/profile nodes.
    
    Args:
        connection: Neo4j connection instance
        app_data: Application data for relationship creation
    """
    try:
        # Determine borrower profile based on application characteristics
        profile_queries = []
        
        if app_data.first_time_buyer:
            profile_queries.append("""
            MATCH (app:MortgageApplication {application_id: $application_id})
            MATCH (bp:BorrowerProfile {profile_name: "FirstTimeBuyer"})
            CREATE (app)-[:MATCHES_PROFILE]->(bp)
            """)
        
        if app_data.military_service:
            profile_queries.append("""
            MATCH (app:MortgageApplication {application_id: $application_id})
            MATCH (bp:BorrowerProfile {profile_name: "Military"})
            CREATE (app)-[:MATCHES_PROFILE]->(bp)
            """)
        
        if app_data.rural_property:
            profile_queries.append("""
            MATCH (app:MortgageApplication {application_id: $application_id})
            MATCH (bp:BorrowerProfile {profile_name: "RuralBuyer"})
            CREATE (app)-[:MATCHES_PROFILE]->(bp)
            """)
        
        # High income/credit profile
        if (app_data.credit_score and app_data.credit_score >= 740 and 
            app_data.monthly_gross_income >= 10000):
            profile_queries.append("""
            MATCH (app:MortgageApplication {application_id: $application_id})
            MATCH (bp:BorrowerProfile {profile_name: "HighIncomeStrong Credit"})
            CREATE (app)-[:MATCHES_PROFILE]->(bp)
            """)
        
        # Execute profile relationship queries
        for query in profile_queries:
            connection.execute_query(query, {"application_id": app_data.application_id})
        
        # Create potential loan program relationships
        program_queries = []
        
        # FHA eligibility
        if (not app_data.credit_score or app_data.credit_score >= 580):
            program_queries.append("""
            MATCH (app:MortgageApplication {application_id: $application_id})
            MATCH (lp:LoanProgram {name: "FHA"})
            CREATE (app)-[:ELIGIBLE_FOR]->(lp)
            """)
        
        # VA eligibility
        if app_data.military_service:
            program_queries.append("""
            MATCH (app:MortgageApplication {application_id: $application_id})
            MATCH (lp:LoanProgram {name: "VA"})
            CREATE (app)-[:ELIGIBLE_FOR]->(lp)
            """)
        
        # USDA eligibility
        if app_data.rural_property and (not app_data.credit_score or app_data.credit_score >= 640):
            program_queries.append("""
            MATCH (app:MortgageApplication {application_id: $application_id})
            MATCH (lp:LoanProgram {name: "USDA"})
            CREATE (app)-[:ELIGIBLE_FOR]->(lp)
            """)
        
        # Conventional eligibility
        if (not app_data.credit_score or app_data.credit_score >= 620):
            program_queries.append("""
            MATCH (app:MortgageApplication {application_id: $application_id})
            MATCH (lp:LoanProgram {name: "Conventional"})
            CREATE (app)-[:ELIGIBLE_FOR]->(lp)
            """)
        
        # Execute program relationship queries
        for query in program_queries:
            connection.execute_query(query, {"application_id": app_data.application_id})
            
        logger.info(f"Created relationships for application {app_data.application_id}")
        
    except Exception as e:
        logger.warning(f"Error creating application relationships: {e}")


def get_application_data(application_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve application data from Neo4j by application ID.
    
    Args:
        application_id: Unique application identifier
        
    Returns:
        Dictionary with application data or None if not found
    """
    try:
        connection = get_neo4j_connection()
        
        query = """
        MATCH (app:MortgageApplication {application_id: $application_id})
        RETURN app
        """
        
        result = connection.execute_query(query, {"application_id": application_id})
        record = result.single()
        
        if record:
            return dict(record["app"])
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving application {application_id}: {e}")
        return None


def list_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all applications, optionally filtered by status.
    
    Args:
        status: Optional status filter
        
    Returns:
        List of application dictionaries
    """
    try:
        connection = get_neo4j_connection()
        
        if status:
            query = """
            MATCH (app:MortgageApplication {current_status: $status})
            RETURN app
            ORDER BY app.received_date DESC
            """
            result = connection.execute_query(query, {"status": status})
        else:
            query = """
            MATCH (app:MortgageApplication)
            RETURN app
            ORDER BY app.received_date DESC
            """
            result = connection.execute_query(query)
        
        return [dict(record["app"]) for record in result]
        
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        return []


def update_application_status(application_id: str, new_status: str, notes: Optional[str] = None) -> bool:
    """
    Update the status of an application.
    
    Args:
        application_id: Application to update
        new_status: New status value
        notes: Optional notes about the status change
        
    Returns:
        True if successful, False otherwise
    """
    try:
        connection = get_neo4j_connection()
        
        query = """
        MATCH (app:MortgageApplication {application_id: $application_id})
        SET app.current_status = $new_status,
            app.updated_timestamp = datetime()
        """
        
        params = {
            "application_id": application_id,
            "new_status": new_status
        }
        
        if notes:
            query += ", app.workflow_notes = $notes"
            params["notes"] = notes
        
        query += " RETURN app.application_id as id"
        
        result = connection.execute_query(query, params)
        
        if result.single():
            logger.info(f"Updated application {application_id} status to {new_status}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        return False
