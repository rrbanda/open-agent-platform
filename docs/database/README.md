# Database Integration Documentation

This folder contains comprehensive documentation for integrating AI agents with the Neo4j mortgage database system.

## 📋 Document Overview

### 🏗️ **COMPLETE_AI_AGENT_SYSTEM_SUMMARY.md**
**Complete system architecture and integration guide**

Contains:
- Database schema overview (23+ node types)
- Business rule categories (Underwriting, Compliance, Risk Assessment, etc.)
- Agent integration patterns
- System capabilities and technical advantages
- Performance characteristics and query patterns

**Use for**: Understanding the overall system architecture and how agents integrate with the database.

### 🔍 **AI_AGENT_CYPHER_QUERIES.md**
**Comprehensive Cypher query library for mortgage operations**

Contains:
- 50+ production-ready Cypher queries
- Loan program analysis queries
- Underwriting rule evaluations  
- Document requirement patterns
- Risk assessment and qualification queries
- Application status management
- Business rule validation patterns

**Use for**: Copy-paste ready queries for agent tool development.

### 🔄 **AI_AGENT_COMPLETE_WORKFLOW_QUERIES.md**
**End-to-end workflow and multi-step process queries**

Contains:
- Complete mortgage application workflows
- Multi-agent coordination patterns
- Status progression tracking
- Document workflow management
- Quality assurance and validation workflows
- Reporting and analytics queries

**Use for**: Implementing complex multi-step mortgage processing workflows.

## 🎯 Quick Start Guide

### 1. **System Understanding**
Start with `COMPLETE_AI_AGENT_SYSTEM_SUMMARY.md` to understand:
- How the database is structured
- What business rules are available
- How agents should interact with the system

### 2. **Query Development**  
Use `AI_AGENT_CYPHER_QUERIES.md` to:
- Find relevant queries for your agent's needs
- Understand query patterns and best practices
- Adapt queries for specific use cases

### 3. **Workflow Implementation**
Reference `AI_AGENT_COMPLETE_WORKFLOW_QUERIES.md` to:
- Implement end-to-end processes
- Coordinate between multiple agents
- Track application status and progress

## 🔌 Database Connection

These queries work with the [mortgage-db repository](https://github.com/rrbanda/mortgage-db) deployment:

```python
# Example: Using queries in agent tools
from mortgage_processor.utils.db import get_neo4j_connection

def my_agent_tool():
    connection = get_neo4j_connection()
    
    with connection.driver.session(database='mortgage') as session:
        # Copy query from documentation
        query = """
        MATCH (lp:LoanProgram {name: $program_name})
        MATCH (lp)-[:HAS_REQUIREMENT]->(req:QualificationRequirement)
        RETURN lp, collect(req) as requirements
        """
        
        result = session.run(query, {"program_name": "CONVENTIONAL"})
        return [dict(record) for record in result]
```

## 📊 Query Categories

| **Category** | **Document** | **Example Queries** |
|---|---|---|
| **Loan Programs** | Cypher Queries | Get program details, requirements, eligibility |
| **Underwriting** | Cypher Queries | DTI calculations, credit analysis, risk assessment |
| **Documents** | Cypher Queries | Required docs, verification status, completeness |
| **Applications** | Cypher Queries | Status tracking, data retrieval, updates |
| **Workflows** | Workflow Queries | End-to-end processes, multi-step operations |
| **Business Rules** | All Documents | Rule evaluation, compliance checking, validation |

## 🛠️ Development Tips

### **Query Adaptation**
- Replace parameter values with your agent's variables
- Modify RETURN clauses to get the data your agent needs
- Add WHERE clauses for specific filtering

### **Performance**
- The database is indexed for common query patterns
- Use parameters (`$param`) instead of string concatenation
- Limit result sets with appropriate WHERE clauses

### **Error Handling**
- Queries include NULL handling with OPTIONAL MATCH
- Results may be empty - always check before processing
- Use database warnings to identify missing relationships/properties

## 🔗 Related Files

- **Agent Tools**: `../../v1/src/mortgage_processor/agents/*/tools/`
- **Database Utils**: `../../v1/src/mortgage_processor/utils/db/`
- **Configuration**: `../../v1/config.yaml`

## 💡 Contributing

When adding new queries or documentation:
1. Follow existing patterns and naming conventions
2. Include parameter examples and expected results
3. Document any new business rules or relationships
4. Test queries against the deployed mortgage-db system
