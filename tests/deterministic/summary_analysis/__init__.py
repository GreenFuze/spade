"""
RIG Effectiveness Summary Analysis Module

This module provides comprehensive analysis of RIG (Repository Information Generation)
effectiveness across multiple repositories of varying complexity.

Main components:
- config: Configuration constants and repository definitions
- templates: Text templates for report generation
- complexity: Complexity calculation and formatting functions
- visualizations: Chart generation for academic papers
- report_generator: Markdown report generation
- main: Main execution orchestration

Usage:
    # Run as script
    python -m summary_analysis

    # Or import and use programmatically
    from summary_analysis.main import main
    main()
"""

__version__ = "2.0.0"
__author__ = "RIG Analysis Team"

# Export main function for easy access
from .main import main

__all__ = ['main']
