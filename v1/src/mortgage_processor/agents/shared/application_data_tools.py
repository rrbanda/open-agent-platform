"""
Shared Application Data Tools

These tools provide a consistent interface for all agents to access stored application data.
This eliminates the confusion of having multiple storage modules and provides clean, 
discoverable tools for application data operations.
"""

import logging
from langchain_core.tools import tool

# Import from the primary storage module (utils/db)
try:
    from mortgage_processor.utils.db import (
        get_application_data,
        list_applications,
        initialize_connection
    )
except ImportError:
    # Fallback import path
    from ...utils.db import (
        get_application_data,
        list_applications,
        initialize_connection
    )

logger = logging.getLogger(__name__)


@tool
def get_stored_application_data(application_id: str) -> str:
    """
    Retrieve stored application data by application ID.
    
    This tool allows any agent to access previously stored application information
    without needing to re-ask the customer for basic details.
    
    Args:
        application_id: The application ID (e.g., "APP_20250926_090605_JOH")
        
    Returns:
        String containing the application data or error message
    """
    try:
        if not application_id or not application_id.strip():
            return "❌ Error: Application ID is required"
            
        # Initialize database connection
        initialize_connection()
        
        # Get application data from storage
        app_data = get_application_data(application_id.strip())
        
        if not app_data:
            return f"❌ Application {application_id} not found in storage"
            
        # Format the application data nicely
        result = f"""
✅ **STORED APPLICATION DATA**

**Application ID:** {app_data.get('application_id', application_id)}
**Status:** {app_data.get('current_status', 'Unknown')}
**Received:** {app_data.get('received_date', 'Unknown')}

**👤 PERSONAL INFO:**
• Name: {app_data.get('first_name', '')} {app_data.get('last_name', '')}
• DOB: {app_data.get('date_of_birth', 'Not provided')}
• Phone: {app_data.get('phone', 'Not provided')}
• Email: {app_data.get('email', 'Not provided')}
• SSN: {app_data.get('ssn', 'Not provided')}

**🏠 ADDRESS INFO:**
• Current Address: {app_data.get('current_street', '')}, {app_data.get('current_city', '')}, {app_data.get('current_state', '')} {app_data.get('current_zip', '')}
• Years at Address: {app_data.get('years_at_address', 'Not provided')}

**💼 EMPLOYMENT INFO:**
• Employer: {app_data.get('employer_name', 'Not provided')}
• Job Title: {app_data.get('job_title', 'Not provided')}
• Years Employed: {app_data.get('years_employed', 'Not provided')}
• Monthly Income: ${app_data.get('monthly_gross_income', 0):,.2f}
• Employment Type: {app_data.get('employment_type', 'Not provided')}

**💰 LOAN INFO:**
• Purpose: {app_data.get('loan_purpose', 'Not provided')}
• Loan Amount: ${app_data.get('loan_amount', 0):,.2f}
• Property Address: {app_data.get('property_address', 'Not provided')}
• Property Value: ${app_data.get('property_value', 0):,.2f}
• Property Type: {app_data.get('property_type', 'Not provided')}
• Occupancy: {app_data.get('occupancy_type', 'Not provided')}

**💳 FINANCIAL INFO:**
• Credit Score: {app_data.get('credit_score') or 'Not provided'}
• Monthly Debts: ${app_data.get('monthly_debts', 0):,.2f}
• Liquid Assets: ${app_data.get('liquid_assets', 0):,.2f}
• Down Payment: ${app_data.get('down_payment', 0):,.2f}

**🎯 SPECIAL PROGRAMS:**
• First-Time Buyer: {'Yes' if app_data.get('first_time_buyer') else 'No'}
• Military Service: {'Yes' if app_data.get('military_service') else 'No'}
• Rural Property: {'Yes' if app_data.get('rural_property') else 'No'}

**📊 PROCESSING INFO:**
• Completion: {app_data.get('completion_percentage', 0):.1f}%
• Next Agent: {app_data.get('next_agent', 'Not specified')}
• Notes: {app_data.get('workflow_notes', 'No notes')}
"""
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error retrieving application data: {e}")
        return f"❌ Error retrieving application {application_id}: {str(e)}"


@tool  
def list_stored_applications(status_filter: str = "") -> str:
    """
    List all stored applications, optionally filtered by status.
    
    This tool helps agents see all applications in the system and their current status.
    
    Args:
        status_filter: Optional status to filter by (e.g., "RECEIVED", "PROCESSING")
        
    Returns:
        String listing all applications matching the criteria
    """
    try:
        # Initialize database connection
        initialize_connection()
        
        # Get applications from storage
        if status_filter and status_filter.strip():
            applications = list_applications(status_filter.strip().upper())
        else:
            applications = list_applications()
            
        if not applications:
            filter_msg = f" with status '{status_filter}'" if status_filter else ""
            return f"No applications found{filter_msg}"
            
        result = ["📋 **STORED APPLICATIONS**\n"]
        
        for i, app in enumerate(applications[:10], 1):  # Show max 10
            app_id = app.get('application_id', 'Unknown')
            name = f"{app.get('first_name', '')} {app.get('last_name', '')}".strip()
            status = app.get('current_status', 'Unknown')
            loan_amount = app.get('loan_amount', 0)
            received = app.get('received_date', 'Unknown')[:10]  # Just date part
            
            result.append(f"{i}. **{app_id}**")
            result.append(f"   • Applicant: {name or 'Not provided'}")
            result.append(f"   • Status: {status}")
            result.append(f"   • Loan Amount: ${loan_amount:,.0f}")
            result.append(f"   • Received: {received}")
            result.append("")
            
        if len(applications) > 10:
            result.append(f"... and {len(applications) - 10} more applications")
            
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        return f"❌ Error listing applications: {str(e)}"


@tool
def find_application_by_name(applicant_name: str) -> str:
    """
    Find applications by applicant name.
    
    This tool helps agents find existing applications when they only have the customer's name.
    
    Args:
        applicant_name: Full or partial name of the applicant
        
    Returns:
        String with matching applications or "not found" message
    """
    try:
        if not applicant_name or not applicant_name.strip():
            return "❌ Error: Applicant name is required"
            
        # Initialize database connection
        initialize_connection()
        
        name_query = applicant_name.strip()
        
        # Get all applications and search by name
        all_apps = list_applications()
        matching_apps = []
        
        for app in all_apps:
            first_name = app.get('first_name', '').lower()
            last_name = app.get('last_name', '').lower()
            full_name = f"{first_name} {last_name}".strip()
            
            if (name_query.lower() in full_name or 
                name_query.lower() in first_name or 
                name_query.lower() in last_name):
                matching_apps.append(app)
                
        if not matching_apps:
            return f"❌ No applications found for '{applicant_name}'"
            
        result = [f"✅ **APPLICATIONS FOR '{applicant_name.upper()}'**\n"]
        
        for i, app in enumerate(matching_apps, 1):
            app_id = app.get('application_id', 'Unknown')
            name = f"{app.get('first_name', '')} {app.get('last_name', '')}".strip()
            status = app.get('current_status', 'Unknown') 
            phone = app.get('phone', 'Not provided')
            
            result.append(f"{i}. **{app_id}** - {name}")
            result.append(f"   • Status: {status}")
            result.append(f"   • Phone: {phone}")
            result.append("")
            
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Error finding applications by name: {e}")
        return f"❌ Error searching for applications: {str(e)}"


def validate_application_data_tools() -> bool:
    """Validate that the application data tools work correctly."""
    try:
        # Test tools with sample data
        result1 = list_stored_applications.invoke({"status_filter": ""})
        result2 = find_application_by_name.invoke({"applicant_name": "test"})
        result3 = get_stored_application_data.invoke({"application_id": "nonexistent"})
        
        # Should not crash and should return strings
        return (isinstance(result1, str) and 
                isinstance(result2, str) and 
                isinstance(result3, str))
                
    except Exception as e:
        logger.error(f"Application data tools validation failed: {e}")
        return False
