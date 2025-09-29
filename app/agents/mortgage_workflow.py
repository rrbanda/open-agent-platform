"""
Production Multi-Agent Routing Coordinator
Following LangGraph's official routing pattern with structured output

Based on LangGraph documentation: 
https://langchain-ai.github.io/langgraph/tutorials/introduction/#routing

This implements the routing workflow pattern where an LLM classifies 
input and directs it to specialized followup tasks.
"""

from typing import TypedDict, Annotated, Sequence, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Import individual agents
from .application_agent import create_application_agent
from .mortgage_advisor_agent import create_mortgage_advisor_agent  
from .document_agent import create_document_agent
from .appraisal_agent import create_appraisal_agent
from .underwriting_agent import create_underwriting_agent

# Import LLM
try:
    from utils import get_llm, extract_message_content_and_files
except ImportError:
    from utils import get_llm, extract_message_content_and_files


class MortgageRoutingState(TypedDict):
    """State for multi-agent mortgage routing workflow"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    route_decision: str


class RouteClassification(BaseModel):
    """Schema for structured output routing classification"""
    agent: Literal[
        "mortgage_advisor_agent", 
        "application_agent", 
        "document_agent", 
        "appraisal_agent", 
        "underwriting_agent"
    ] = Field(description="The specialist agent best suited to handle this mortgage request")


def create_routing_node():
    """Create LLM-powered routing node following LangGraph routing pattern"""
    
    llm = get_llm()
    classifier = llm.with_structured_output(RouteClassification)
    
    def router(state: MortgageRoutingState):
        """Route classification using LLM with structured output"""
        
        messages = state["messages"]
        if not messages:
            return {"route_decision": "mortgage_advisor_agent"}
        
        # Get user message content (handle both string and list formats)
        user_messages = [msg for msg in messages if getattr(msg, 'type', None) == 'human']
        if not user_messages:
            return {"route_decision": "mortgage_advisor_agent"}
        
        last_user_message = user_messages[-1]
        
        # AGENTIC: Let the LLM classifier SEE and REASON about file content
        try:
            # Extract full content including files for agent reasoning
            parsed_content = extract_message_content_and_files(last_user_message)
            content = parsed_content['full_content']  # LLM sees everything
            
        except Exception as e:
            # Fallback to original parsing logic if enhanced parser fails
            content = ""
            if hasattr(last_user_message, 'content'):
                raw_content = last_user_message.content
                if isinstance(raw_content, list):
                    content = raw_content[0].get('text', '') if raw_content and isinstance(raw_content[0], dict) else str(raw_content[0]) if raw_content else ""
                else:
                    content = str(raw_content)
        
        if not content.strip():
            return {"route_decision": "mortgage_advisor_agent"}
        
        # Build conversation context for context-aware routing
        conversation_context = ""
        if len(messages) >= 2:
            # Get the last few messages to understand conversation flow
            recent_messages = messages[-3:] if len(messages) >= 3 else messages[-2:]
            for msg in recent_messages:
                sender = "Agent" if getattr(msg, 'type', None) == 'ai' else "User"
                msg_content = getattr(msg, 'content', str(msg))
                if isinstance(msg_content, list) and msg_content:
                    # Handle multimodal content
                    msg_content = str(msg_content[0].get('text', '')) if isinstance(msg_content[0], dict) else str(msg_content[0])
                elif not isinstance(msg_content, str):
                    msg_content = str(msg_content)
                conversation_context += f"{sender}: {msg_content[:200]}...\n" if len(msg_content) > 200 else f"{sender}: {msg_content}\n"
        
        # CONTEXT-AWARE LLM classification
        classification_prompt = [
            SystemMessage(content="""You are an intelligent mortgage processing coordinator. Use conversation context to understand the flow and route appropriately.

**CONTEXT-AWARE ROUTING GUIDELINES:**

**CONVERSATION CONTEXT RULES (HIGHEST PRIORITY):**
- If the previous agent asked a specific question and the user is providing an answer, route BACK to that same agent
- If ApplicationAgent asked for personal info (name, DOB, etc.) and user provides it, route to "application_agent"
- If DocumentAgent asked about documents and user responds, route to "document_agent"
- Continue with the same agent until their task is completely finished

**ROUTING GUIDELINES:**

**mortgage_advisor_agent**: General guidance, loan options, rates, eligibility
- Use when: Customer asks questions about loan types, rates, qualification
- Keywords: "options", "rates", "qualify", "first-time buyer", "programs"

**application_agent**: Formal application submission AND data collection
- Use when: Customer wants to start/complete formal application OR is providing application data
- Keywords: "apply", "application", "submit", "URLA", "form", names, addresses, income, employment
- IMPORTANT: If user is answering application questions (name, DOB, address, etc.), stay with application_agent

**document_agent**: Document processing, verification, uploads
- Use when: Customer uploads documents OR mentions specific documents
- IMPORTANT: If you see "UPLOADED DOCUMENTS:" in the content, route here
- Documents include: paystubs, W2s, bank statements, tax returns, ID, etc.

**appraisal_agent**: Property valuation, market analysis
- Use when: Questions about property value, appraisals, market conditions
- Keywords: "value", "appraisal", "market", "worth", "price"

**underwriting_agent**: Credit analysis, approval decisions
- Use when: Credit-related questions, approval status, lending decisions
- Keywords: "approved", "credit", "decision", "underwriting"

**REASONING APPROACH:**
1. **FIRST**: Check conversation context - if user is responding to an agent's question, continue with that agent
2. Check if documents are uploaded - if yes, route to document_agent
3. Look at the main intent of the customer's request
4. Route based on PRIMARY need and conversation flow

Prioritize conversation continuity over keyword matching."""),
            HumanMessage(content=f"Recent conversation:\n{conversation_context}\n\nCurrent user message: {content}")
        ]
        
        try:
            classification = classifier.invoke(classification_prompt)
            return {"route_decision": classification.agent}
        except Exception:
            # Fallback to mortgage advisor for any classification errors
            return {"route_decision": "mortgage_advisor_agent"}
    
    return router


def route_to_agent(state: MortgageRoutingState) -> Literal["mortgage_advisor_agent", "application_agent", "document_agent", "appraisal_agent", "underwriting_agent"]:
    """Conditional edge function following LangGraph routing pattern"""
    return state["route_decision"]


def create_agent_node(agent_name: str, agent):
    """Create agentic execution node that provides enhanced content to agents"""
    
    def agent_execution(state: MortgageRoutingState):
        """Execute agent with enhanced message content for intelligent processing"""
        
        messages = state["messages"]
        if not messages:
            return {"messages": []}
            
        # For document-related agents, enhance the last user message with file content
        if agent_name == "document_agent" and messages:
            try:
                # Get the last user message
                user_messages = [msg for msg in messages if getattr(msg, 'type', None) == 'human']
                if user_messages:
                    last_user_msg = user_messages[-1]
                    
                    # Extract full content including files
                    parsed_content = extract_message_content_and_files(last_user_msg)
                    
                    # Log file processing for DocumentAgent
                    if parsed_content.get('has_files'):
                        print(f"🔍 DocumentAgent processing {parsed_content.get('file_count', 0)} uploaded files")
                    
                    # Create enhanced message for agent with all file content visible
                    from langchain_core.messages import HumanMessage
                    
                    # Use first 2000 chars of full content to avoid RHOAI issues
                    content_to_send = parsed_content['full_content']
                    if len(content_to_send) > 2000:
                        content_to_send = content_to_send[:2000] + "\n\n[Content truncated for processing...]"
                        print(f"🔍 DEBUG: Truncated large content from {len(parsed_content['full_content'])} to {len(content_to_send)} chars")
                    
                    enhanced_message = HumanMessage(content=content_to_send)
                    
                    # Replace last user message with enhanced version
                    enhanced_messages = messages[:-1] + [enhanced_message]
                    
                    result = agent.invoke({"messages": enhanced_messages})
                    return {"messages": result["messages"]}
                    
            except Exception as e:
                # Fallback to original messages if enhancement fails
                pass
        
        # Default execution for other agents or fallback
        result = agent.invoke({"messages": messages})
        return {"messages": result["messages"]}
    
    return agent_execution


def create_mortgage_routing_workflow():
    """
    Create production mortgage routing workflow
    Following LangGraph's official routing pattern
    """
    
    # Initialize all specialist agents
    application_agent = create_application_agent()
    mortgage_advisor_agent = create_mortgage_advisor_agent() 
    document_agent = create_document_agent()
    appraisal_agent = create_appraisal_agent()
    underwriting_agent = create_underwriting_agent()
    
    # Build routing workflow
    workflow = StateGraph(MortgageRoutingState)
    
    # Add routing node
    routing_classifier = create_routing_node()
    workflow.add_node("router", routing_classifier)
    
    # Add specialist agent nodes
    workflow.add_node("mortgage_advisor_agent", create_agent_node("mortgage_advisor_agent", mortgage_advisor_agent))
    workflow.add_node("application_agent", create_agent_node("application_agent", application_agent))
    workflow.add_node("document_agent", create_agent_node("document_agent", document_agent))
    workflow.add_node("appraisal_agent", create_agent_node("appraisal_agent", appraisal_agent))
    workflow.add_node("underwriting_agent", create_agent_node("underwriting_agent", underwriting_agent))
    
    # Entry point: routing
    workflow.add_edge("__start__", "router")
    
    # Conditional routing based on classification
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "mortgage_advisor_agent": "mortgage_advisor_agent",
            "application_agent": "application_agent", 
            "document_agent": "document_agent",
            "appraisal_agent": "appraisal_agent",
            "underwriting_agent": "underwriting_agent"
        }
    )
    
    # All agents terminate workflow after execution
    workflow.add_edge("mortgage_advisor_agent", END)
    workflow.add_edge("application_agent", END)
    workflow.add_edge("document_agent", END)
    workflow.add_edge("appraisal_agent", END)
    workflow.add_edge("underwriting_agent", END)
    
    return workflow.compile()


def create_mortgage_workflow():
    """
    Create production-grade mortgage workflow
    
    Returns compiled LangGraph workflow implementing intelligent routing
    with LLM-based classification for mortgage specialist selection
    """
    return create_mortgage_routing_workflow()
