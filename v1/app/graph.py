#!/usr/bin/env python3
"""
LangGraph App Graph for Mortgage Processing System V1
Provides the compiled routing workflow for LangGraph dev command

This creates a production-ready routing workflow that intelligently routes
users to the appropriate specialist agent based on LLM classification.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mortgage_processor.agents.mortgage_workflow import create_mortgage_workflow

# Create the routing workflow (compiled LangGraph with intelligent routing)
# LangGraph dev handles persistence automatically
app = create_mortgage_workflow()
