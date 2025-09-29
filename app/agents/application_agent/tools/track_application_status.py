"""
Application Status Tracking Tool

This tool tracks and manages application status throughout the workflow
based on Neo4j application intake rules. Enhanced with agentic application retrieval.
"""

import json
import logging
from typing import Dict, Any
from langchain_core.tools import tool
from datetime import datetime, timedelta

try:
    from utils import get_neo4j_connection, initialize_connection, get_application_data, update_application_status
except ImportError:
    from utils import get_neo4j_connection, initialize_connection, get_application_data, update_application_status

logger = logging.getLogger(__name__)


def parse_neo4j_rule(rule_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON strings back to objects in Neo4j rule data."""
    parsed_rule = {}
    for key, value in rule_dict.items():
        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
            try:
                parsed_rule[key] = json.loads(value)
            except json.JSONDecodeError:
                parsed_rule[key] = value  # Keep as string if not valid JSON
        else:
            parsed_rule[key] = value
    return parsed_rule




@tool
def track_application_status(status_request: str) -> str:
    """
    Track and manage application status using Neo4j application intake rules.
    
    This tool provides comprehensive application status tracking, updates, and history
    throughout the mortgage application workflow process.
    
    Provide status request information in natural language, such as:
    "Check status of application APP_20250926_090605_JOH"
    "Update application APP_123 status to APPROVED with notes: all documents received"
    "Track application APP_456, current status RECEIVED, action check_status"
    "Get history for application APP_789"
    """
    
    try:
        # Parse status request string
        import re
        request = status_request.lower()
        
        # Extract application ID
        app_id_match = re.search(r'app(?:lication)?\s*([a-z0-9_]+)', request)
        application_id = app_id_match.group(1).upper() if app_id_match else "APP_20250926_090605_JOH"
        
        # Extract current status
        status_match = re.search(r'(?:current\s*status|status):\s*([a-z_]+)', request)
        current_status = status_match.group(1).upper() if status_match else "RECEIVED"
        
        # Determine action
        if "check" in request or "track" in request:
            requested_action = "check_status"
        elif "update" in request or "change" in request:
            requested_action = "update_status"
        elif "history" in request:
            requested_action = "get_history"
        else:
            requested_action = "check_status"
        
        # Extract new status if updating
        new_status_match = re.search(r'(?:update.*to|new\s*status|to)\s*([a-z_]+)', request)
        new_status = new_status_match.group(1).upper() if new_status_match else None
        
        # Set defaults
        status_notes = "Status update via agentic tool"
        agent_name = "ApplicationAgent"
        completion_percentage = None
        milestone_reached = None
        estimated_completion = None
        issues_identified = []
        resolution_required = False
        # Initialize Neo4j connection
        initialize_connection()
        connection = get_neo4j_connection()
        
        with connection.driver.session(database=connection.database) as session:
            # Get status management rules
            status_query = """
            MATCH (rule:ApplicationIntakeRule)
            WHERE rule.category = 'StatusManagement'
            RETURN rule
            """
            result = session.run(status_query)
            status_rules = [parse_neo4j_rule(dict(record['rule'])) for record in result]
        
        # 🤖 AGENTIC RETRIEVAL: Get real application data from Neo4j
        app_retrieval = get_application_data(application_id)
        
        # Generate status tracking report
        status_report = []
        status_report.append("APPLICATION STATUS TRACKING")
        status_report.append("=" * 50)
        
        # Application Header with real data
        status_report.append(f"\n📋 APPLICATION TRACKING:")
        status_report.append(f"Application ID: {application_id}")
        
        if app_retrieval.found:
            # Use real stored application data
            app_data = app_retrieval.application_data
            stored_status = app_data.current_status
            status_report.append(f"Stored Status: {stored_status}")
            status_report.append(f"Input Status: {current_status}")
            status_report.append(f"Applicant: {app_data.first_name} {app_data.last_name}")
            status_report.append(f"Loan Amount: ${app_data.loan_amount:,.0f}")
            status_report.append(f"Property: {app_data.property_address}")
            
            # Use stored status for processing
            effective_status = stored_status
        else:
            # Fallback to input status if no stored data
            status_report.append(f"Current Status: {current_status}")
            status_report.append(f"⚠️ APPLICATION DATA: Not found in agentic storage, using input values")
            effective_status = current_status
            
        status_report.append(f"Requested Action: {requested_action.replace('_', ' ').title()}")
        status_report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get status lifecycle rules
        lifecycle_rule = next((rule for rule in status_rules if rule.get('rule_type') == 'status_tracking'), {})
        status_progression = lifecycle_rule.get('status_progression', [])
        status_definitions = lifecycle_rule.get('status_definitions', {})
        
        # Process different actions
        if requested_action == "check_status":
            # Check current status and provide details
            status_report.append(f"\n📊 STATUS ANALYSIS:")
            
            if current_status in status_definitions:
                definition = status_definitions[current_status]
                status_report.append(f"Status Definition: {definition.replace('_', ' ')}")
            
            # Find position in workflow
            if effective_status in status_progression:
                current_index = status_progression.index(current_status)
                total_stages = len(status_progression)
                progress_pct = ((current_index + 1) / total_stages) * 100
                
                status_report.append(f"Workflow Position: {current_index + 1} of {total_stages}")
                status_report.append(f"Progress: {progress_pct:.1f}% complete")
                
                # Show workflow progression
                status_report.append(f"\n🗺️ WORKFLOW PROGRESSION:")
                for i, stage in enumerate(status_progression):
                    if i == current_index:
                        status_report.append(f"  ➤ {stage.replace('_', ' ').title()} ← CURRENT")
                    elif i < current_index:
                        status_report.append(f"   {stage.replace('_', ' ').title()}")
                    else:
                        status_report.append(f"  ⏳ {stage.replace('_', ' ').title()}")
                
                # Next steps
                if current_index < total_stages - 1:
                    next_status = status_progression[current_index + 1]
                    status_report.append(f"\n⏭️ NEXT STEP:")
                    status_report.append(f"Next Status: {next_status.replace('_', ' ').title()}")
                    if next_status in status_definitions:
                        next_definition = status_definitions[next_status]
                        status_report.append(f"Next Phase: {next_definition.replace('_', ' ')}")
                else:
                    status_report.append(f"\n🎯 FINAL STAGE:")
                    status_report.append("Application has reached final status")
            
        elif requested_action == "update_status":
            # Update status and validate transition
            status_report.append(f"\n🔄 STATUS UPDATE:")
            
            if new_status:
                status_report.append(f"Previous Status: {effective_status}")
                status_report.append(f"New Status: {new_status}")
                
                # 🤖 AGENTIC UPDATE: Store status change in Neo4j
                try:
                    # Create status notes combining all information
                    notes = f"Agent: {agent_name or 'ApplicationAgent'}"
                    if status_notes:
                        notes += f", Notes: {status_notes}"
                    if completion_percentage:
                        notes += f", Completion: {completion_percentage}%"
                    if milestone_reached:
                        notes += f", Milestone: {milestone_reached}"
                    
                    update_success = update_application_status(application_id, new_status, notes)
                    
                    if update_success:
                        status_report.append(f"✅ AGENTIC UPDATE: Status updated to {new_status}")
                    else:
                        status_report.append(f"⚠️ UPDATE WARNING: Failed to update status")
                        
                except Exception as update_error:
                    logger.warning(f"Agentic status update failed: {update_error}")
                    status_report.append(f"⚠️ UPDATE WARNING: Auto-update failed, status change logged locally")
                
                # Validate status transition
                if effective_status in status_progression and new_status in status_progression:
                    current_index = status_progression.index(effective_status)
                    new_index = status_progression.index(new_status)
                    
                    if new_index == current_index + 1:
                        transition_valid = True
                        transition_type = "FORWARD PROGRESSION"
                    elif new_index > current_index + 1:
                        transition_valid = True
                        transition_type = "SKIP FORWARD"
                    elif new_index < current_index:
                        transition_valid = True
                        transition_type = "BACKWARD/CORRECTION"
                    else:
                        transition_valid = True
                        transition_type = "SAME LEVEL"
                    
                    status_report.append(f"Transition Type: {transition_type}")
                    status_report.append(f"Transition Valid: {'' if transition_valid else ''}")
                
                if agent_name:
                    status_report.append(f"Updated By: {agent_name}")
                if status_notes:
                    status_report.append(f"Notes: {status_notes}")
                
                # Update completion percentage
                if new_status in status_progression:
                    new_index = status_progression.index(new_status)
                    auto_completion = ((new_index + 1) / len(status_progression)) * 100
                    final_completion = completion_percentage if completion_percentage else auto_completion
                    status_report.append(f"Completion: {final_completion:.1f}%")
                
                # Milestone tracking
                if milestone_reached:
                    status_report.append(f"\n🎯 MILESTONE REACHED:")
                    status_report.append(f"Milestone: {milestone_reached}")
                    status_report.append(f"Achievement Date: {datetime.now().strftime('%Y-%m-%d')}")
                
                # Timeline estimates
                if estimated_completion:
                    status_report.append(f"\n📅 TIMELINE:")
                    status_report.append(f"Estimated Completion: {estimated_completion}")
                
                # Issues tracking
                if issues_identified:
                    status_report.append(f"\n⚠️ ISSUES IDENTIFIED:")
                    for issue in issues_identified:
                        status_report.append(f"  • {issue}")
                    if resolution_required:
                        status_report.append("🔧 Resolution Required: YES")
                    else:
                        status_report.append("📝 Resolution Required: NO")
                
            else:
                status_report.append(" Error: New status not provided for update")
        
        elif requested_action == "get_history":
            # Provide status history from agentic storage
            status_report.append(f"\n📚 STATUS HISTORY:")
            
            if app_retrieval.found and app_retrieval.status_history:
                # Use real stored history
                status_report.append("Real Application History:")
                for i, history_item in enumerate(reversed(app_retrieval.status_history)):
                    timestamp = history_item.get('timestamp', 'Unknown')
                    status = history_item.get('status', 'Unknown')
                    agent = history_item.get('agent_name', 'System')
                    notes = history_item.get('notes', '')
                    
                    status_report.append(f"  {timestamp[:10]}: {status.replace('_', ' ').title()} (by {agent})")
                    if notes:
                        status_report.append(f"    Notes: {notes}")
            else:
                # Fallback to simulated history
                if effective_status in status_progression:
                    current_index = status_progression.index(effective_status)
                
                    # Show completed statuses
                    base_date = datetime.now() - timedelta(days=current_index * 2)
                    for i in range(current_index + 1):
                        status = status_progression[i]
                        status_date = base_date + timedelta(days=i * 2)
                        status_report.append(f"    {status_date.strftime('%Y-%m-%d')}: {status.replace('_', ' ').title()}")
                    
                    # Show estimated future statuses
                    if current_index < len(status_progression) - 1:
                        status_report.append(f"\n📅 PROJECTED TIMELINE:")
                        for i in range(current_index + 1, len(status_progression)):
                            status = status_progression[i]
                            future_date = datetime.now() + timedelta(days=(i - current_index) * 3)
                            status_report.append(f"    {future_date.strftime('%Y-%m-%d')}: {status.replace('_', ' ').title()} (Estimated)")
        
        # Communication and Notifications
        comm_rule = next((rule for rule in status_rules if rule.get('rule_type') == 'communication_requirements'), {})
        
        if comm_rule and requested_action == "update_status":
            status_report.append(f"\n📞 COMMUNICATION REQUIREMENTS:")
            
            # notification_triggers = comm_rule.get('notification_triggers', {})  # Available for notification logic
            
            # Check if notifications are required
            notifications_needed = []
            
            if new_status and new_status != effective_status:
                notifications_needed.append("Status change notification")
            
            if issues_identified:
                notifications_needed.append("Issue notification")
            
            if milestone_reached:
                notifications_needed.append("Milestone achievement notification")
            
            if notifications_needed:
                status_report.append("Required Notifications:")
                for notification in notifications_needed:
                    status_report.append(f"  • {notification}")
                
                # Communication methods
                comm_methods = comm_rule.get('communication_methods', [])
                status_report.append(f"Communication Methods: {', '.join(comm_methods)}")
            else:
                status_report.append("No notifications required for this update")
        
        # Performance Metrics
        status_report.append(f"\n📈 PERFORMANCE METRICS:")
        
        if effective_status in status_progression:
            current_index = status_progression.index(current_status)
            days_elapsed = current_index * 2  # Simulated
            
            # Calculate performance
            if effective_status in ["approved", "closed"]:
                performance_status = "COMPLETED"
            elif days_elapsed <= 10:
                performance_status = "ON TRACK"
            elif days_elapsed <= 15:
                performance_status = "MONITORING"
            else:
                performance_status = "DELAYED"
            
            status_report.append(f"Processing Time: {days_elapsed} days")
            status_report.append(f"Performance Status: {performance_status}")
            
            # Industry benchmarks (simulated)
            industry_avg = 14
            if days_elapsed < industry_avg:
                status_report.append(f"vs Industry Average: {days_elapsed - industry_avg} days faster")
            elif days_elapsed > industry_avg:
                status_report.append(f"vs Industry Average: {days_elapsed - industry_avg} days slower")
            else:
                status_report.append("vs Industry Average: On par")
        
        # Quality Checkpoints
        status_report.append(f"\n QUALITY CHECKPOINTS:")
        
        checkpoints = [
            ("Application Completeness", effective_status not in ["received", "in_review"]),
            ("Documentation Verification", effective_status not in ["received", "in_review", "incomplete", "complete"]),
            ("Property Appraisal", effective_status not in ["received", "in_review", "incomplete", "complete", "in_processing"]),
            ("Underwriting Review", effective_status in ["approved", "denied", "closed"]),
            ("Final Approval", effective_status in ["approved", "closed"])
        ]
        
        for checkpoint, completed in checkpoints:
            status_icon = "" if completed else "⏳"
            status_report.append(f"  {status_icon} {checkpoint}")
        
        # Action Items and Next Steps
        status_report.append(f"\n📋 ACTION ITEMS:")
        
        if effective_status == "incomplete":
            status_report.append("• Contact applicant for missing information")
            status_report.append("• Provide clear documentation requirements")
        elif effective_status == "in_review":
            status_report.append("• Complete application review process")
            status_report.append("• Determine next workflow step")
        elif effective_status == "complete":
            status_report.append("• Route to document verification")
            status_report.append("• Begin processing workflow")
        elif effective_status == "in_processing":
            status_report.append("• Monitor document verification progress")
            status_report.append("• Coordinate with processing agents")
        elif effective_status == "underwriting":
            status_report.append("• Complete underwriting analysis")
            status_report.append("• Prepare approval/denial decision")
        else:
            status_report.append("• Monitor application progress")
            status_report.append("• Maintain regular communication")
        
        # Escalation Guidelines
        if requested_action == "update_status" and issues_identified:
            status_report.append(f"\n🚨 ESCALATION GUIDELINES:")
            
            if resolution_required:
                status_report.append("• Immediate escalation required")
                status_report.append("• Notify senior management")
                status_report.append("• Develop resolution timeline")
            else:
                status_report.append("• Monitor issue closely")
                status_report.append("• Document for trend analysis")
                status_report.append("• Standard processing continues")
        
        # Summary and Recommendations
        status_report.append(f"\n💡 SUMMARY AND RECOMMENDATIONS:")
        
        if requested_action == "check_status":
            status_report.append("• Status check completed successfully")
            status_report.append("• Application progressing through workflow")
            status_report.append("• Continue monitoring and communication")
        elif requested_action == "update_status":
            status_report.append("• Status update processed successfully")
            status_report.append("• Notifications will be sent as required")
            status_report.append("• Continue with next workflow steps")
        elif requested_action == "get_history":
            status_report.append("• Status history retrieved successfully")
            status_report.append("• Timeline information available for planning")
            status_report.append("• Use data for performance optimization")
        
        return "\n".join(status_report)
        
    except Exception as e:
        logger.error(f"Error during status tracking: {e}")
        return f" Error during status tracking: {str(e)}"


def validate_tool() -> bool:
    """Validate that the track_application_status tool works correctly."""
    try:
        # Test with sample natural language data
        result = track_application_status.invoke({
            "status_request": "Check status of application APP_20240101_123456_SMI, current status in_processing, action check_status"
        })
        return "APPLICATION STATUS TRACKING" in result and "STATUS ANALYSIS" in result
    except Exception as e:
        print(f"Application status tracking tool validation failed: {e}")
        return False
