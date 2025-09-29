"""
Mortgage Processor V1 - Production Agentic System

This package provides a complete end-to-end agentic mortgage processing system
with 5 specialized agents, intelligent router workflow, and 200+ Neo4j-powered business rules.

## Quick Start - End-to-End Processing

```python
from app.agents import create_mortgage_workflow

# Create router workflow for intelligent agent routing
workflow = create_mortgage_workflow()
response = workflow.invoke({
    "messages": [("user", "I want to apply for a mortgage")]
})
# Router automatically routes to the appropriate specialist agent
```

## Quick Start - Individual Agents

```python
from app.agents import (
    create_application_agent,
    create_mortgage_advisor_agent,
    create_document_agent,
    create_appraisal_agent,
    create_underwriting_agent
)

# Initialize any specific agent
agent = create_application_agent()
response = agent.invoke({"messages": [("user", "I want to apply for a mortgage")]})
```

## Architecture

- **Data-Driven**: All business logic stored in Neo4j knowledge graph
- **LangGraph ReAct**: Built-in memory, streaming, and tool calling
- **Modular Design**: Each agent in separate package with comprehensive tests
- **Production Ready**: Professional testing with LangSmith evaluations

## Agents

**Coordination Layer:**
- **Router Workflow**: End-to-end workflow orchestration with intelligent LLM-based routing

**Specialized Agents:**
1. **ApplicationAgent**: Mortgage application intake & URLA generation
2. **MortgageAdvisorAgent**: Customer guidance & loan recommendations  
3. **DocumentAgent**: Document verification & ID validation
4. **AppraisalAgent**: Property valuation & market analysis
5. **UnderwritingAgent**: Credit analysis & lending decisions

## Database Setup

Ensure Neo4j is running locally with database "mortgage":

```python
from app.utils import initialize_connection
# Note: mortgage_data_loader was removed during utils restructuring

initialize_connection()
load_all_mortgage_data()  # Loads 200+ business rules
```

Ready for production deployment and compelling demos!
"""

__version__ = "1.0.0"
__author__ = "Mortgage Processor Team"

# Core package imports
from .agents import (
    create_application_agent,
    create_mortgage_advisor_agent, 
    create_document_agent,
    create_appraisal_agent,
    create_underwriting_agent,
    create_mortgage_workflow
)

from .utils import initialize_connection
from .utils.config import AppConfig

__all__ = [
    # Agent creators (5 specialized agents + router workflow)
    "create_application_agent",
    "create_mortgage_advisor_agent",
    "create_document_agent", 
    "create_appraisal_agent",
    "create_underwriting_agent",
    "create_mortgage_workflow",
    
    # Core utilities
    "initialize_connection",
    "AppConfig",
    
    # Package metadata
    "__version__",
    "__author__"
]
