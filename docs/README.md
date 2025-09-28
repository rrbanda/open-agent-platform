# Documentation

This folder contains documentation for the Mortgage Processing AI Agent System.

## 📂 Folder Structure

```
docs/
├── README.md                   # This file - documentation overview
└── database/                   # Database integration documentation
    ├── COMPLETE_AI_AGENT_SYSTEM_SUMMARY.md      # Complete system overview
    ├── AI_AGENT_CYPHER_QUERIES.md               # Cypher query examples
    └── AI_AGENT_COMPLETE_WORKFLOW_QUERIES.md    # Workflow-specific queries
```

## 🗄️ Database Documentation

The `database/` folder contains comprehensive documentation for integrating with the [mortgage-db repository](https://github.com/rrbanda/mortgage-db):

### **COMPLETE_AI_AGENT_SYSTEM_SUMMARY.md**
- Complete system architecture overview
- Database schema descriptions  
- Integration patterns for AI agents
- Business rule categories and usage

### **AI_AGENT_CYPHER_QUERIES.md**
- Comprehensive collection of Cypher queries for mortgage operations
- Query patterns for loan program analysis
- Underwriting rule evaluations
- Document requirement queries
- Risk assessment patterns

### **AI_AGENT_COMPLETE_WORKFLOW_QUERIES.md**
- End-to-end workflow query examples
- Multi-step mortgage processing operations
- Agent coordination query patterns
- Status tracking and workflow management

## 🎯 Usage

These documents are reference materials for:

1. **Agent Developers** - Understanding how to query the mortgage database
2. **System Integration** - Examples of connecting agents to database operations
3. **Business Logic** - Understanding mortgage domain rules and processes
4. **Query Development** - Copy-paste ready Cypher queries for common operations

## 🏗️ Architecture Context

This agent system connects to a separate [mortgage-db repository](https://github.com/rrbanda/mortgage-db) which provides:
- Complete database infrastructure
- 200+ business rules
- Self-initializing container deployment
- Production-ready mortgage domain data

The agent system (this repo) provides:
- AI agent tools and logic
- Minimal runtime database utilities
- Agent workflow orchestration
- Application data storage

## 📖 How to Use These Docs

1. Start with `COMPLETE_AI_AGENT_SYSTEM_SUMMARY.md` for system overview
2. Reference `AI_AGENT_CYPHER_QUERIES.md` for specific query patterns
3. Use `AI_AGENT_COMPLETE_WORKFLOW_QUERIES.md` for complex workflows
4. Adapt queries for your specific agent tool implementations

## 🔗 Related Resources

- [Mortgage Database Repository](https://github.com/rrbanda/mortgage-db) - Complete database system
- Agent Tools: `v1/src/mortgage_processor/agents/` - Current agent implementations
- Database Utils: `v1/src/mortgage_processor/utils/db/` - Connection utilities
