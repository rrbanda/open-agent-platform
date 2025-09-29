#!/usr/bin/env python3
"""
End-to-End Mortgage Application Demo

Real workflow using agent system API:
1. New person applies for mortgage
2. Submits application through system API
3. Application gets processed by existing agents
4. Applicant sees final result

Uses the agent system API at http://127.0.0.1:2024
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import json
import requests

console = Console()

# Agent system API configuration
LANGGRAPH_URL = "http://127.0.0.1:2024"

def check_server_status():
    """Check if agent system is running"""
    try:
        response = requests.get(f"{LANGGRAPH_URL}/ok")
        return response.status_code == 200
    except:
        return False

def get_assistant():
    """Get the mortgage processing assistant"""
    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/assistants/search",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assistants = response.json()
        
        # Find mortgage processing assistant
        for assistant in assistants:
            if assistant.get("graph_id") == "mortgage_processing":
                return assistant["assistant_id"]
        
        return None
    except Exception as e:
        console.print(f"[red]Error finding assistant: {e}[/red]")
        return None

def create_thread():
    """Create a new thread using agent system API"""
    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/threads",
            json={},
            headers={"Content-Type": "application/json"}
        )
        return response.json()["thread_id"]
    except Exception as e:
        console.print(f"[red]Error creating thread: {e}[/red]")
        return None

def invoke_assistant(assistant_id, thread_id, message):
    """Invoke assistant using agent system API"""
    try:
        payload = {
            "input": {"messages": [{"role": "user", "content": message}]},
            "assistant_id": assistant_id
        }
        
        response = requests.post(
            f"{LANGGRAPH_URL}/threads/{thread_id}/runs/wait",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    except Exception as e:
        console.print(f"[red]Error invoking assistant: {e}[/red]")
        return None

def setup_system():
    """Setup connection to agent system"""
    console.print(Panel(
        "[bold green]🏦 Connecting to Agent System[/bold green]\nUsing system API at http://127.0.0.1:2024",
        border_style="green"
    ))
    
    if not check_server_status():
        console.print("[red]❌ Agent system not accessible[/red]")
        console.print("[yellow]Please ensure the agent system is running[/yellow]")
        return None, None
    
    console.print("✅ [green]Connected to agent system[/green]")
    
    # Get assistant
    assistant_id = get_assistant()
    if not assistant_id:
        console.print("[red]❌ Failed to find mortgage processing assistant[/red]")
        return None, None
    
    console.print(f"✅ [green]Found assistant: {assistant_id}[/green]")
    
    # Create conversation thread
    thread_id = create_thread()
    if not thread_id:
        console.print("[red]❌ Failed to create conversation thread[/red]")
        return None, None
    
    console.print(f"✅ [green]Thread created: {thread_id}[/green]\n")
    return assistant_id, thread_id

def show_execution_details(result, step_name):
    """Display tool calls and agent responses from system API"""
    console.print(f"\n[bold magenta]🔍 EXECUTION DETAILS - {step_name}[/bold magenta]")
    
    if not result:
        console.print("[red]No result received[/red]")
        return
    
    # Extract messages from agent system response
    messages = result.get("messages", [])
    
    for msg in messages:
        msg_type = msg.get("type", "unknown")
        content = msg.get("content", "")
        
        if msg_type == "human":
            console.print(f"[blue]👤 USER INPUT:[/blue] {content[:150]}...")
            
        elif msg_type == "ai":
            # Check for tool calls
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name", "Unknown")
                    tool_args = tool_call.get("args", {})
                    console.print(f"[cyan]🛠️ Tool Call:[/cyan] {tool_name}")
                    
                    # Show transfer details
                    if "transfer" in tool_name.lower() and "agent" in tool_args:
                        console.print(f"[yellow]  ↳ Routing to: {tool_args['agent']}[/yellow]")
            else:
                # Regular AI response
                if content:
                    console.print(f"[blue]🤖 Agent Response:[/blue] {content[:200]}...")
                    
        elif msg_type == "tool":
            # Tool results
            tool_name = msg.get("name", "Unknown")
            console.print(f"[green]📤 Tool Result from {tool_name}:[/green] {content[:150]}...")

def step_1_consultation(assistant_id, thread_id):
    """Step 1: Initial consultation through system API"""
    console.print(Panel(
        "[bold yellow]📋 STEP 1: Initial Consultation[/bold yellow]\nUsing agent system API to route to appropriate specialist",
        border_style="yellow"
    ))
    
    user_input = "Hi, I'm Sarah Johnson, a first-time homebuyer. I make $95,000/year as a software engineer and have $60,000 saved. I'm looking at a $450,000 home in Austin, TX. What are my mortgage options?"
    
    console.print(f"[bold blue]👤 Sarah:[/bold blue] {user_input}")
    console.print("🔄 [yellow]Sending to agent system...[/yellow]")
    
    result = invoke_assistant(assistant_id, thread_id, user_input)
    
    # Show execution details
    show_execution_details(result, "CONSULTATION")
    
    return result

def step_2_application(assistant_id, thread_id):
    """Step 2: Application submission through system API"""
    console.print(Panel(
        "[bold cyan]📝 STEP 2: Application Submission[/bold cyan]\nUsing system API with database persistence",
        border_style="cyan"
    ))
    
    app_input = """I'd like to submit my complete mortgage application:

Personal Info:
- Name: Sarah Johnson
- SSN: 123-45-6789  
- DOB: 1994-08-15
- Phone: 512-555-0123
- Email: sarah.johnson@email.com

Current Address:
- 2100 Guadalupe St, Austin, TX 78705
- Living here for 3 years

Employment:
- Employer: TechCorp Austin
- Position: Senior Software Engineer
- 4 years with company  
- Monthly income: $7,916

Loan Details:
- Purpose: Purchase
- Loan amount: $390,000
- Property: 1234 Hill Country Dr, Austin, TX 78746
- Property value: $450,000
- Property type: Single family home
- Primary residence

Financial Info:
- Credit score: 720
- Monthly debts: $850
- Assets: $60,000
- Down payment: $60,000
- First-time buyer: Yes"""

    console.print(f"[bold blue]👤 Sarah:[/bold blue] I'd like to submit my complete mortgage application with all details.")
    console.print("🔄 [yellow]Sending to system API...[/yellow]")
    
    result = invoke_assistant(assistant_id, thread_id, app_input)
    
    # Show execution details
    show_execution_details(result, "APPLICATION SUBMISSION")
    
    # Extract application ID from tool results
    app_id = None
    if result:
        messages = result.get("messages", [])
        for msg in messages:
            content = str(msg.get("content", ""))
            if "APP_" in content:
                import re
                match = re.search(r'APP_\w+', content)
                if match:
                    app_id = match.group(0)
                    console.print(f"[green]📋 Application ID: {app_id}[/green]")
                    break
    
    return result, app_id

def step_3_tracking(assistant_id, thread_id, app_id):
    """Step 3: Application tracking through system API"""
    console.print(Panel(
        "[bold magenta]⚙️ STEP 3: Application Status Tracking[/bold magenta]\nUsing system API with database retrieval",
        border_style="magenta"
    ))
    
    if app_id:
        track_input = f"Can you check the status of my application? My application ID is {app_id}."
    else:
        track_input = "Can you check the status of my mortgage application that I just submitted?"
    
    console.print(f"[bold blue]👤 Sarah:[/bold blue] {track_input}")
    console.print("🔄 [yellow]Sending to system API...[/yellow]")
    
    result = invoke_assistant(assistant_id, thread_id, track_input)
    
    # Show execution details
    show_execution_details(result, "STATUS TRACKING")
    
    return result

def step_4_result(assistant_id, thread_id):
    """Step 4: Final result through system API"""
    console.print(Panel(
        "[bold green]🎯 STEP 4: Application Processing Result[/bold green]\nFinal workflow outcome via system API",
        border_style="green"
    ))
    
    result_input = "What's the final status of my mortgage application? Has it been approved for the next steps?"
    
    console.print(f"[bold blue]👤 Sarah:[/bold blue] {result_input}")
    console.print("🔄 [yellow]Sending to system API...[/yellow]")
    
    result = invoke_assistant(assistant_id, thread_id, result_input)
    
    # Show execution details
    show_execution_details(result, "FINAL RESULT")
    
    return result

def show_workflow_summary():
    """Show the workflow that was executed"""
    console.print(Panel(
        "[bold blue]📊 E2E Workflow Summary[/bold blue]\nUsing agent system API",
        border_style="blue"
    ))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Step", style="cyan")
    table.add_column("API Used", style="yellow")
    table.add_column("Endpoint", style="green")
    table.add_column("Result", style="blue")
    
    table.add_row("Setup", "System API", "POST /assistants/search", "Found mortgage assistant")
    table.add_row("Thread", "System API", "POST /threads", "Created conversation thread")
    table.add_row("Consultation", "System API", "POST /threads/{id}/runs/wait", "Advisor guidance")
    table.add_row("Application", "System API", "POST /threads/{id}/runs/wait", "Database persistence")
    table.add_row("Tracking", "System API", "POST /threads/{id}/runs/wait", "Status retrieval")
    table.add_row("Result", "System API", "POST /threads/{id}/runs/wait", "Workflow completion")
    
    console.print(table)
    
    console.print("\n✨ [bold green]Features Demonstrated:[/bold green]")
    console.print("• Used proper agent system API endpoints")
    console.print("• Assistant discovery via /assistants/search")
    console.print("• Thread management via /threads")
    console.print("• Execution via /threads/{id}/runs/wait")
    console.print("• Database persistence across interactions")
    console.print("• Production-grade API integration")

def main():
    """Run the E2E mortgage demo with agent system API"""
    console.print(Panel(
        "[bold green]🏠 E2E Mortgage Demo[/bold green]\nUsing Agent System API\nWorkflow: Apply → Process → Result\nConnecting to system API at http://127.0.0.1:2024",
        border_style="green"
    ))
    
    try:
        # System setup
        assistant_id, thread_id = setup_system()
        if not assistant_id or not thread_id:
            return
        
        # Show applicant info
        console.print(Panel(
            "[bold blue]👤 Applicant Profile[/bold blue]\nSarah Johnson: First-time buyer, $95K income, $60K down, $450K home target",
            border_style="blue"
        ))
        
        input("Press Enter to start mortgage workflow with agent system...")
        
        # Step 1: Consultation through system API
        step_1_result = step_1_consultation(assistant_id, thread_id)
        input("\nPress Enter to proceed to application submission...")
        
        # Step 2: Application through system API  
        step_2_result, app_id = step_2_application(assistant_id, thread_id)
        input("\nPress Enter to track application status...")
        
        # Step 3: Tracking through system API
        step_3_result = step_3_tracking(assistant_id, thread_id, app_id)
        input("\nPress Enter to see final result...")
        
        # Step 4: Final result through system API
        step_4_result = step_4_result(assistant_id, thread_id)
        input("\nPress Enter to see workflow summary...")
        
        # Summary
        show_workflow_summary()
        
        console.print(Panel(
            "[bold green]🎉 E2E Demo Complete![/bold green]\nAgent system integration successful!",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n\n[red]Demo error: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()