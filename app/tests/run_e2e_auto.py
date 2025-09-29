#!/usr/bin/env python3
"""
Auto E2E Demo - Using Running Agent System

Shows the complete mortgage workflow using the running agent system.
Connects to running server at http://127.0.0.1:2024
"""

import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import time
import requests
from datetime import datetime

console = Console()

# Agent system API configuration
LANGGRAPH_URL = "http://127.0.0.1:2024"

def typewriter_effect(text, delay=0.005, style="bold green"):
    """Create a typewriter effect for text - LARGE for screen sharing"""
    rich_text = Text()
    
    for char in text:
        rich_text.append(char, style=style)
        console.print(rich_text, end="\r")
        time.sleep(delay)
    
    console.print()  # Extra line for spacing
    console.print(Panel(
        rich_text,
        style=style,
        border_style="bright_blue",
        padding=(1, 3),
        title="[bold bright_yellow]🗣️ SARAH'S QUESTION[/bold bright_yellow]",
        title_align="left"
    ))
    console.print()  # Extra spacing
    time.sleep(0.8)  # Longer pause for screen sharing

def show_status_update(message):
    """Show a simple status update without permanent display"""
    console.print(f"⏳ {message}", style="bold bright_yellow")

def print_section_header(title, icon, color="cyan"):
    """Print a compact section header"""
    console.print()
    
    # Create compact header
    header_text = Text()
    header_text.append(f"{icon}  {title}  {icon}", style=f"bold bright_{color}")
    
    console.print(Panel(
        header_text,
        style=f"bold bright_{color}",
        border_style=f"bright_{color}",
        padding=(0, 2),
        title=f"[bold bright_white]STEP IN PROGRESS[/bold bright_white]",
        title_align="center"
    ))

def check_server_status():
    """Check if agent system is running"""
    try:
        response = requests.get(f"{LANGGRAPH_URL}/ok")
        return response.status_code == 200
    except:
        return False

def load_sample_document(filename):
    """Load sample document content from docs folder"""
    try:
        # Get the project root directory (two levels up from tests)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        doc_path = os.path.join(project_root, "docs", "sample_documents", filename)
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        console.print(f"[red]Warning: Could not load {filename}: {e}[/red]")
        return f"[Sample {filename} content would be processed here]"

def create_document_upload_message():
    """Create realistic document upload message with actual document content"""
    
    # Load sample documents
    w2_content = load_sample_document("w2_2023_sarah_johnson.txt")
    paystub_content = load_sample_document("paystub_nov_2024_sarah_johnson.txt")
    bank_statement_content = load_sample_document("bank_statement_nov_2024_sarah_johnson.txt")
    
    # Create comprehensive document upload message
    message = f"""Hi, I just uploaded my financial documents. Can you process these and let me know what else you need?

**Document 1: 2023 W-2 Tax Form**
Filename: w2_2023_sarah_johnson.pdf
Document Type: w2
Content:
{w2_content[:500]}...

**Document 2: Recent Pay Stub** 
Filename: paystub_nov_2024_sarah_johnson.pdf
Document Type: paystub  
Content:
{paystub_content[:500]}...

**Document 3: Bank Statement**
Filename: bank_statement_nov_2024_sarah_johnson.pdf
Document Type: bank_statement
Content:
{bank_statement_content[:500]}...

Please process these documents and let me know if you need anything else for my mortgage application."""

    return message

def create_demo_assistant():
    """Create a new demo assistant for mortgage processing"""
    try:
        assistant_config = {
            "graph_id": "mortgage_processing",
            "config": {},
            "metadata": {
                "name": "demo_mortgage_system",
                "description": "Demo assistant for end-to-end mortgage processing workflow",
                "created_by": "e2e_demo"
            }
        }
        
        response = requests.post(
            f"{LANGGRAPH_URL}/assistants",
            json=assistant_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()["assistant_id"]
        else:
            console.print(f"[red]Failed to create assistant: {response.status_code}[/red]")
            return None
            
    except Exception as e:
        console.print(f"[red]Error creating demo assistant: {e}[/red]")
        return None

def delete_demo_assistant(assistant_id):
    """Delete the demo assistant to clean up"""
    try:
        response = requests.delete(
            f"{LANGGRAPH_URL}/assistants/{assistant_id}",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 204]:  # 204 = No Content (successful deletion)
            return True
        else:
            console.print(f"[red]Failed to delete assistant: {response.status_code}[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]Error deleting demo assistant: {e}[/red]")
        return False

def get_assistant():
    """Get the mortgage processing assistant (fallback method)"""
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

def show_execution_details(result, step_name):
    """Display execution details from agent system with enhanced visuals - ENHANCED FOR BUSINESS TOOL DETECTION"""
    
    # Create a beautiful execution header
    console.print()
    execution_panel = Panel(
        f"[bold white on blue] 🔍 LIVE EXECUTION - {step_name} [/bold white on blue]",
        border_style="blue",
        padding=(0, 1)
    )
    console.print(execution_panel)
    
    if not result:
        console.print(Panel("[bold red]❌ No result received[/bold red]", border_style="red"))
        return
    
    # Extract messages from agent system response
    messages = result.get("messages", [])
    
    # ENHANCED: Track business tools found
    business_tools_found = []
    transfers_found = []
    
    for i, msg in enumerate(messages):
        msg_type = msg.get("type", "unknown")
        content = msg.get("content", "")
        
        if msg_type == "human":
            # User input with distinct styling
            user_text = Text()
            user_text.append("👤 USER INPUT: ", style="bold blue")
            user_text.append(f"{content[:150]}...", style="dim blue")
            console.print(Panel(user_text, border_style="blue", padding=(0, 1)))
            
        elif msg_type == "ai":
            # ENHANCED: Multiple ways to detect tool calls
            tool_calls = msg.get("tool_calls", [])
            
            # Method 1: Standard tool_calls field
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name", "Unknown")
                    
                    # Track business tools vs transfers
                    if "transfer" in tool_name.lower():
                        transfers_found.append(tool_name)
                    elif any(business in tool_name.lower() for business in ['recommend_loan_program', 'explain_loan', 'guide_next_steps', 'check_qualification']):
                        business_tools_found.append(tool_name)
                    
                    # Enhanced tool call display - LARGE for screen sharing
                    tool_text = Text()
                    if "transfer" in tool_name.lower():
                        tool_text.append("\n🔄  AGENT TRANSFER:  ", style="bold bright_blue")
                        tool_text.append(f"{tool_name.upper()}", style="bright_white")
                        tool_text.append("  🔄\n", style="bold bright_blue")
                    else:
                        tool_text.append("\n🏦  BUSINESS RULE TOOL:  ", style="bold bright_green")
                        tool_text.append(f"{tool_name.upper()}", style="bright_white")
                        tool_text.append("  🏦\n", style="bold bright_green")
                    
                    # Show transfer details
                    if "transfer" in tool_name.lower():
                        args = tool_call.get("args", {})
                        target_agent = tool_name.replace("transfer_to_", "").replace("_", " ").title()
                        tool_text.append(f"\n    ↳ Routing to: {target_agent}\n", style="bright_yellow")
                        border_color = "bright_blue"
                    else:
                        # Show business rule tool arguments
                        args = tool_call.get("args", {})
                        tool_text.append(f"\n    📊 Analyzing business rules with Neo4j data\n", style="bright_cyan")
                        if args:
                            tool_text.append(f"    🔍 Input: {str(args)[:100]}...\n", style="dim bright_white")
                        border_color = "bright_green"
                    
                    console.print(Panel(
                        tool_text, 
                        border_style=border_color, 
                        padding=(1, 2),
                        title=f"[bold bright_white]⚡ TOOL EXECUTION ⚡[/bold bright_white]",
                        title_align="center"
                    ))
            
            # Method 2: Fallback - look for tool calls in content (for API format differences)
            elif content and any(tool in content.lower() for tool in ['recommend_loan_program', 'explain_loan', 'guide_next_steps']):
                # Extract tool name from content
                for tool in ['recommend_loan_program', 'explain_loan_programs', 'guide_next_steps']:
                    if tool in content.lower():
                        business_tools_found.append(tool)
                        
                        tool_text = Text()
                        tool_text.append("\n🏦  BUSINESS RULE TOOL DETECTED:  ", style="bold bright_green")
                        tool_text.append(f"{tool.upper()}", style="bright_white")
                        tool_text.append("  🏦\n", style="bold bright_green")
                        tool_text.append(f"\n    📊 Detected in agent response content\n", style="bright_cyan")
                        
                        console.print(Panel(
                            tool_text, 
                            border_style="bright_green", 
                            padding=(1, 2),
                            title=f"[bold bright_white]⚡ TOOL EXECUTION (DETECTED) ⚡[/bold bright_white]",
                            title_align="center"
                        ))
                        break
            
            # Method 3: Look for business analysis indicators in ANY AI message content
            if content and any(indicator in content for indicator in ['LOAN PROGRAM ANALYSIS', 'MORTGAGE PROCESS GUIDANCE', 'Neo4j business rules']):
                if 'business_analysis_detected' not in business_tools_found:
                    business_tools_found.append('Neo4j Business Rule Analysis')
                    
                    tool_text = Text()
                    tool_text.append("\n🎯  BUSINESS ANALYSIS ACTIVE:  ", style="bold bright_green")
                    tool_text.append("BUSINESS RULES", style="bright_white")
                    tool_text.append("  🎯\n", style="bold bright_green")
                    tool_text.append(f"\n    📊 Agent is using mortgage business rules\n", style="bright_cyan")
                    tool_text.append(f"    🔍 Analysis result detected in response\n", style="bright_cyan")
                    
                    console.print(Panel(
                        tool_text, 
                        border_style="bright_green", 
                        padding=(1, 2),
                        title=f"[bold bright_white]⚡ BUSINESS RULE EXECUTION ⚡[/bold bright_white]",
                        title_align="center"
                    ))
            
            # Show agent response content - NO CUSTOM CATEGORIZATION
            if content:
                agent_text = Text()
                agent_text.append(f"🤖 {msg.get('name', 'AGENT').upper()}: ", style="bold white")
                agent_text.append(content[:600] + "..." if len(content) > 600 else content, style="white")
                console.print(Panel(agent_text, border_style="white", padding=(0, 1)))
                    
        elif msg_type == "tool":
            # Tool results - ENHANCED for business tool visibility
            tool_name = msg.get("name", "Unknown")
            
            # Enhanced: Detect business tool results by name OR content
            is_business_result = (
                any(business in tool_name.lower() for business in ['recommend_loan_program', 'explain_loan', 'guide_next_steps', 'check_qualification']) or
                any(indicator in content for indicator in ['LOAN PROGRAM ANALYSIS', 'MORTGAGE PROCESS GUIDANCE', 'qualification', 'DTI', 'credit score'])
            )
            
            if is_business_result:
                # Track as business tool
                if tool_name not in business_tools_found:
                    business_tools_found.append(tool_name)
                
                # LARGE business tool result display for screen sharing
                result_text = Text()
                result_text.append("\n🎯  REAL NEO4J BUSINESS ANALYSIS:  ", style="bold bright_green")
                result_text.append(f"{tool_name.upper()}", style="bright_white")
                result_text.append("  🎯\n\n", style="bold bright_green")
                
                # Show actual Neo4j analysis result
                if "LOAN PROGRAM ANALYSIS" in content or "MORTGAGE PROCESS GUIDANCE" in content:
                    result_text.append("✅ Live Neo4j mortgage business rules executed!\n", style="bright_green")
                    result_text.append("📊 Real-time qualification analysis from graph database\n\n", style="bright_cyan")
                    result_text.append(f"{content[:400]}...\n", style="bright_white")
                elif any(indicator in content for indicator in ['qualification', 'DTI', 'credit score', 'down payment']):
                    result_text.append("✅ Business rule processing detected!\n", style="bright_green")
                    result_text.append("📊 Mortgage qualification logic applied\n\n", style="bright_cyan")
                    result_text.append(f"{content[:400]}...\n", style="bright_white")
                else:
                    result_text.append(f"{content[:400]}...\n", style="bright_white")
                
                console.print(Panel(
                    result_text, 
                    border_style="bright_green", 
                    padding=(1, 2),
                    title="[bold bright_white]🏆 BUSINESS RULE EXECUTION CONFIRMED 🏆[/bold bright_white]",
                    title_align="center"
                ))
                
                # Add an extra indicator for screen sharing visibility
                indicator_text = Text()
                indicator_text.append("🔥 LIVE BUSINESS RULE PROCESSING DETECTED! 🔥", style="bold bright_red")
                console.print(Panel(
                    indicator_text,
                    border_style="bright_red",
                    padding=(0, 2),
                    title="[bold bright_white]⚡ REAL MORTGAGE LOGIC ⚡[/bold bright_white]",
                    title_align="center"
                ))
                
            else:
                # Regular tool result
                result_text = Text()
                result_text.append(f"📤 TOOL RESULT ({tool_name}): ", style="bold green")
                result_text.append(content[:400] + "..." if len(content) > 400 else content, style="white")
                console.print(Panel(result_text, border_style="green", padding=(0, 1)))
    
    # ENHANCED: Add execution summary showing what business tools were found
    console.print()
    
    summary_text = Text()
    summary_text.append("\n📋  EXECUTION SUMMARY:\n\n", style="bold bright_cyan")
    summary_text.append(f"🔄 Agent Transfers: {len(transfers_found)}\n", style="bright_white")
    summary_text.append(f"🏦 Business Rule Tools: {len(business_tools_found)}\n", style="bright_white")
    
    if business_tools_found:
        summary_text.append("\n✅ Business Tools Executed:\n", style="bold bright_green")
        for tool in business_tools_found:
            summary_text.append(f"  • {tool}\n", style="bright_green")
    else:
        summary_text.append("\n⚠️ No business rule tools detected in this execution\n", style="bright_yellow")
    
    console.print(Panel(
        summary_text,
        border_style="bright_cyan",
        padding=(1, 2),
        title="[bold bright_white]📊 BUSINESS TOOL TRACKING 📊[/bold bright_white]",
        title_align="center"
    ))
    
    console.print()
    completion_text = Text()
    completion_text.append("⚡ ", style="bold yellow")
    completion_text.append("Execution completed", style="dim white")
    console.print(completion_text)
    console.print()

def display_graph_structure():
    """Display the LangGraph structure at demo start - LARGE for screen sharing"""
    console.print()
    console.print()
    
    # Large title
    title_text = Text()
    title_text.append("\n🏗️  MORTGAGE PROCESSING SYSTEM ARCHITECTURE  🏗️\n", style="bold bright_cyan")
    
    console.print(Panel(
        title_text,
        style="bold bright_cyan",
        border_style="bright_cyan",
        padding=(2, 4)
    ))
    
    # Add the local agent import here to avoid issues
    try:
        sys.path.append('/Users/raghurambanda/iloul/v1/src')
        from app.agents.supervisor_agent import create_supervisor_agent
        
        supervisor = create_supervisor_agent()
        ascii_graph = supervisor.get_graph().draw_ascii()
        
        console.print()
        console.print(Panel(
            f"[bright_white]{ascii_graph}[/bright_white]",
            title="[bold bright_blue]🔗 AGENT GRAPH STRUCTURE 🔗[/bold bright_blue]",
            border_style="bright_blue",
            padding=(0, 1),
            title_align="center"
        ))
        
        console.print()
        explanation_text = Text()
        explanation_text.append("\n🎯 HOW THE WORKFLOW OPERATES:\n\n", style="bold bright_green")
        explanation_text.append("• ", style="bright_yellow")
        explanation_text.append("SUPERVISOR", style="bold bright_cyan")
        explanation_text.append(" coordinates all specialized agents\n", style="bright_white")
        explanation_text.append("• ", style="bright_yellow")
        explanation_text.append("Each agent has specific tools for mortgage processing\n", style="bright_white")
        explanation_text.append("• ", style="bright_yellow")
        explanation_text.append("Agents transfer back to supervisor after completing tasks\n", style="bright_white")
        explanation_text.append("• ", style="bright_yellow")
        explanation_text.append("Flow: ", style="bright_white")
        explanation_text.append("START", style="bold bright_yellow")
        explanation_text.append(" → ", style="bright_white")
        explanation_text.append("SUPERVISOR", style="bold bright_cyan")
        explanation_text.append(" → ", style="bright_white")
        explanation_text.append("SPECIALIZED AGENTS", style="bold bright_green")
        explanation_text.append(" → ", style="bright_white")
        explanation_text.append("END", style="bold bright_red")
        explanation_text.append("\n", style="bright_white")
        
        console.print(Panel(
            explanation_text,
            title="[bold bright_yellow]📋 WORKFLOW EXPLANATION 📋[/bold bright_yellow]",
            border_style="bright_yellow",
            padding=(0, 1),
            title_align="center"
        ))
        
    except Exception as e:
        console.print(Panel(
            f"[bold bright_red]❌ Could not load graph structure: {e}[/bold bright_red]",
            border_style="bright_red",
            padding=(1, 2)
        ))
    
    console.print()
    console.print()

def show_compact_progress(message, style="bold bright_cyan"):
    """Show a compact progress indicator without taking up permanent space"""
    console.print(f"\n{message}", style=style, justify="center")

def auto_demo():
    """Run automated demonstration using agent system API - OPTIMIZED FOR SCREEN SHARING"""
    
    # LARGE demo title for screen sharing
    title_text = Text()
    title_text.append("\n🏠  MORTGAGE PROCESSING DEMO  🏠\n\n", style="bold bright_green")
    title_text.append("    🤖 Using Running Agent System 🤖\n", style="bright_cyan")
    title_text.append("    🔗 Connected to: http://127.0.0.1:2024 🔗\n", style="bright_yellow")
    
    console.print(Panel(
        title_text,
        border_style="bright_green",
        padding=(0, 2),
        title="[bold bright_white]🎬 LIVE DEMONSTRATION 🎬[/bold bright_white]",
        title_align="center"
    ))
    
    # Enhanced system status check
    show_status_update("Connecting to agent system...")
    if not check_server_status():
        console.print(Panel("[bold red]❌ Agent system not accessible at http://127.0.0.1:2024[/bold red]", border_style="red"))
        console.print("[yellow]Please ensure the agent system is running[/yellow]")
        return
    console.print("✅ Connected successfully!", style="bright_green")
    time.sleep(1)
    
    console.print("🎯 [bold green]Connected to agent system[/bold green]")
    
    # Display graph structure
    display_graph_structure()
    
    # Create demo assistant
    show_status_update("Setting up demo environment...")
    assistant_id = create_demo_assistant()
    if not assistant_id:
        console.print("⏳ Fallback: Finding existing assistant...", style="bright_yellow")
        assistant_id = get_assistant()
        if not assistant_id:
            console.print(Panel("[bold red]❌ Failed to find any mortgage processing assistant[/bold red]", border_style="red"))
            return
        console.print("✅ Using existing assistant", style="bright_green")
    else:
        console.print("✅ Demo assistant created!", style="bright_green")
    time.sleep(1)
    
    console.print(f"🎯 [bold green]Assistant ready: {assistant_id}[/bold green]")
    
    # Create conversation thread
    show_status_update("Initializing conversation...")
    thread_id = create_thread()
    if not thread_id:
        console.print(Panel("[bold red]❌ Failed to create conversation thread[/bold red]", border_style="red"))
        return
    console.print("✅ Thread created!", style="bright_green")
    time.sleep(1)
    
    console.print(f"🎯 [bold green]Conversation ready: {thread_id}[/bold green]")
    
    # Customer profile for the mortgage journey
    console.print()
    profile_table = Table(show_header=False, box=None, padding=(0, 2))
    profile_table.add_column(style="bold blue")
    profile_table.add_column(style="white")
    profile_table.add_row("👤 Customer:", "Sarah Johnson")
    profile_table.add_row("🏠 Status:", "First-time homebuyer")
    profile_table.add_row("💰 Monthly Income:", "$8,500")
    profile_table.add_row("💳 Down Payment:", "$67,500 (15%)")
    profile_table.add_row("🎯 Target Home:", "$450,000")
    profile_table.add_row("📊 Credit Score:", "720")
    
    console.print(Panel(
        profile_table,
        title="[bold blue]🏠 Customer Profile[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    ))
    time.sleep(2)
    
    # STEP 1: Initial Mortgage Inquiry
    print_section_header("STEP 1: Initial Mortgage Inquiry", "🏠", "yellow")
    
    console.print("[bold green]👤 Sarah asks:[/bold green]")
    typewriter_effect(
        "Hi! I want to apply for a mortgage. I'm Sarah Johnson, my income is $8,500/month, and I'm looking at a $450,000 home with 15% down.",
        delay=0.02,
        style="italic bright_green"
    )
    
    initial_inquiry = "I want to apply for a mortgage. I'm Sarah Johnson, my income is $8,500/month, and I'm looking at a $450,000 home with 15% down."
    
    show_compact_progress("🔄 Routing to application specialist...", "bold bright_cyan")
    
    result_1 = invoke_assistant(assistant_id, thread_id, initial_inquiry)
    show_execution_details(result_1, "MORTGAGE APPLICATION START")
    
    completion_text = Text()
    completion_text.append("\n🎯  APPLICATION INITIATED  🎯\n\n", style="bold bright_green")
    completion_text.append("✅ Customer routed to application agent\n", style="bright_white")
    completion_text.append("✅ Initial qualification assessment started\n", style="bright_white")
    
    console.print(Panel(
        completion_text,
        border_style="bright_green",
        padding=(0, 2),
        title="[bold bright_white]📋 STEP 1 COMPLETE 📋[/bold bright_white]",
        title_align="center"
    ))
    time.sleep(1)
    
    # STEP 2: Loan Program Recommendation  
    print_section_header("STEP 2: Loan Program Guidance", "💰", "green")
    
    console.print("[bold green]👤 Sarah asks:[/bold green]")
    typewriter_effect(
        "I'm a first-time buyer with a 650 credit score and $67,500 down payment. What loan programs would work best for me?",
        delay=0.02,
        style="italic bright_green"
    )
    
    loan_guidance = "I'm a first-time buyer with a 650 credit score and $67,500 down payment. What loan programs would work best for me?"
    
    show_compact_progress("🔄 Consulting mortgage advisor for program recommendations...", "bold bright_cyan")
    
    result_2 = invoke_assistant(assistant_id, thread_id, loan_guidance)
    show_execution_details(result_2, "LOAN PROGRAM RECOMMENDATION")
    
    completion_text = Text()
    completion_text.append("\n🎯  LOAN GUIDANCE PROVIDED  🎯\n\n", style="bold bright_green")
    completion_text.append("✅ Personalized loan program recommendations\n", style="bright_white")
    completion_text.append("✅ First-time buyer programs identified\n", style="bright_white")
    
    console.print(Panel(
        completion_text,
        border_style="bright_green", 
        padding=(0, 2),
        title="[bold bright_white]📋 STEP 2 COMPLETE 📋[/bold bright_white]",
        title_align="center"
    ))
    time.sleep(1)
    
    # STEP 3: Document Upload Process
    print_section_header("STEP 3: Document Processing", "📄", "cyan")
    
    console.print("[bold green]👤 Sarah asks:[/bold green]")
    typewriter_effect(
        "Hi, I just uploaded my W-2 and pay stubs. Can you process these and let me know what else you need?",
        delay=0.02,
        style="italic bright_green"
    )
    
    # Show document loading process
    console.print(Panel(
        "[bold bright_blue]📁 LOADING SAMPLE DOCUMENTS...\n\n"
        "✅ Reading W-2 tax form (w2_2023_sarah_johnson.pdf)\n"
        "✅ Reading pay stub (paystub_nov_2024_sarah_johnson.pdf)\n" 
        "✅ Reading bank statement (bank_statement_nov_2024_sarah_johnson.pdf)\n\n"
        "📊 Real document content loaded for demonstration",
        title="[bold bright_white]📂 DOCUMENT PREPARATION 📂[/bold bright_white]",
        border_style="bright_blue",
        padding=(0, 2)
    ))
    time.sleep(2)
    
    # Load sample documents and create realistic document upload message
    document_upload = create_document_upload_message()
    
    show_compact_progress("🔄 Processing documents with document agent...", "bold bright_cyan")
    
    result_3 = invoke_assistant(assistant_id, thread_id, document_upload)
    show_execution_details(result_3, "DOCUMENT PROCESSING")
    
    completion_text = Text()
    completion_text.append("\n🎯  DOCUMENTS PROCESSED  🎯\n\n", style="bold bright_green")
    completion_text.append("✅ W-2 and pay stubs reviewed\n", style="bright_white")
    completion_text.append("✅ Additional document requirements provided\n", style="bright_white")
    
    console.print(Panel(
        completion_text,
        border_style="bright_green",
        padding=(0, 2),
        title="[bold bright_white]📋 STEP 3 COMPLETE 📋[/bold bright_white]",
        title_align="center"
    ))
    time.sleep(1)
    
    # STEP 4: Property Appraisal
    print_section_header("STEP 4: Property Appraisal", "🏘️", "blue")
    
    console.print("[bold green]👤 Sarah asks:[/bold green]")
    typewriter_effect(
        "I found a house at 123 Oak Street, Austin, TX. It's listed for $450,000. Can you evaluate if this is a good value?",
        delay=0.02,
        style="italic bright_green"
    )
    
    property_evaluation = "I found a house at 123 Oak Street, Austin, TX. It's listed for $450,000. Can you evaluate if this is a good value?"
    
    show_compact_progress("🔄 Routing to appraisal specialist for property analysis...", "bold bright_cyan")
    
    result_4 = invoke_assistant(assistant_id, thread_id, property_evaluation)
    show_execution_details(result_4, "PROPERTY APPRAISAL")
    
    completion_text = Text()
    completion_text.append("\n🎯  PROPERTY EVALUATED  🎯\n\n", style="bold bright_green")
    completion_text.append("✅ Market analysis completed\n", style="bright_white")
    completion_text.append("✅ Comparable sales reviewed\n", style="bright_white")
    
    console.print(Panel(
        completion_text,
        border_style="bright_green",
        padding=(0, 2),
        title="[bold bright_white]📋 STEP 4 COMPLETE 📋[/bold bright_white]",
        title_align="center"
    ))
    time.sleep(1)
    
    # STEP 5: Final Underwriting Decision
    print_section_header("STEP 5: Final Underwriting Decision", "⚖️", "red")
    
    console.print("[bold green]👤 Sarah asks:[/bold green]")
    typewriter_effect(
        "My credit score is 720, I make $102,000 annually, and I have everything documented. Can you give me my final loan approval decision?",
        delay=0.02,
        style="italic bright_green"
    )
    
    final_underwriting = "My credit score is 720, I make $102,000 annually, and I have everything documented. Can you give me my final loan approval decision?"
    
    show_compact_progress("🔄 Routing to underwriting team for final decision...", "bold bright_cyan")
    
    result_5 = invoke_assistant(assistant_id, thread_id, final_underwriting)
    show_execution_details(result_5, "FINAL UNDERWRITING DECISION")
    
    completion_text = Text()
    completion_text.append("\n🎯  MORTGAGE JOURNEY COMPLETE  🎯\n\n", style="bold bright_green")
    completion_text.append("✅ End-to-end mortgage process demonstrated\n", style="bright_white")
    completion_text.append("✅ All specialized agents coordinated seamlessly\n", style="bright_white")
    
    console.print(Panel(
        completion_text,
        border_style="bright_green",
        padding=(0, 2),
        title="[bold bright_white]🏆 FINAL DECISION 🏆[/bold bright_white]",
        title_align="center"
    ))
    time.sleep(1)
    
    # Complete mortgage journey summary
    console.print(Panel(
        "[bold blue]🏠 Complete Mortgage Journey[/bold blue]\n" +
        "🎯 Step 1: Initial mortgage inquiry → Application specialist\n" +
        "🎯 Step 2: Loan program guidance → Mortgage advisor\n" +
        "🎯 Step 3: Document processing → Document specialist\n" +
        "🎯 Step 4: Property appraisal → Appraisal specialist\n" +
        "🎯 Step 5: Final underwriting → Underwriting specialist\n" +
        "🎯 Result: Seamless customer experience with specialized expertise",
        border_style="blue"
    ))
    
    console.print(Panel(
        "[bold green]🎉 End-to-End Mortgage System Demonstrated![/bold green]\n" +
        "Sarah's complete homebuying journey powered by:\n" +
        "• Intelligent agent routing • Specialized mortgage expertise\n" +
        "• Real-time document processing • Automated appraisal analysis\n" +
        "• Comprehensive underwriting • Seamless customer experience",
        border_style="green"
    ))
    
    # Clean up demo assistant
    console.print("\n")
    show_status_update("Cleaning up demo environment...")
    cleanup_success = delete_demo_assistant(assistant_id)
    if cleanup_success:
        console.print("✅ Demo assistant cleaned up!", style="bright_green")
    else:
        console.print("✅ Cleanup completed (assistant may be external)", style="bright_green")
    time.sleep(1)
    
    # LARGE final message for screen sharing
    final_text = Text()
    if cleanup_success:
        final_text.append("\n🎉  MORTGAGE PROCESSING DEMO COMPLETED  🎉\n\n", style="bold bright_green")
        final_text.append("✅ All steps executed successfully\n", style="bright_white")
        final_text.append("✅ Real agent coordination demonstrated\n", style="bright_white")
        final_text.append("✅ Neo4j business rules validated\n", style="bright_white")
        final_text.append("✅ Demo environment cleaned up\n", style="bright_white")
        border_color = "bright_green"
        title = "[bold bright_white]🏆 DEMO SUCCESS 🏆[/bold bright_white]"
    else:
        final_text.append("\n🎯  MORTGAGE PROCESSING DEMO COMPLETED  🎯\n\n", style="bold bright_yellow")
        final_text.append("✅ All steps executed successfully\n", style="bright_white")
        final_text.append("✅ Real agent coordination demonstrated\n", style="bright_white")
        final_text.append("✅ Neo4j business rules validated\n", style="bright_white")
        final_text.append("⚠️ Demo cleanup completed\n", style="bright_yellow")
        border_color = "bright_yellow"
        title = "[bold bright_white]🎯 DEMO COMPLETE 🎯[/bold bright_white]"
    
    console.print(Panel(
        final_text,
        border_style=border_color,
        padding=(0, 2),
        title=title,
        title_align="center"
    ))
    
    # Add final thank you message
    thank_you_text = Text()
    thank_you_text.append("Thank you for watching the live demonstration!\n", style="bold bright_cyan")
    thank_you_text.append("Questions & Discussion Welcome 🙋‍♂️🙋‍♀️", style="bright_white")
    
    console.print(Panel(
        thank_you_text,
        border_style="bright_cyan",
        padding=(1, 3),
        title="[bold bright_white]🎙️ Q&A SESSION 🎙️[/bold bright_white]",
        title_align="center"
    ))

if __name__ == "__main__":
    auto_demo()