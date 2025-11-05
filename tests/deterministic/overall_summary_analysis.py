"""
Overall Summary Analysis Generator (Thin Wrapper)

This script is a lightweight wrapper around the summary_analysis module.
All logic has been moved into the summary_analysis module for better
organization and maintainability.

The module structure allows for:
- No hard-coded values (all in config.py)
- Easy text updates (all templates in templates.py)
- Clean separation of concerns
- Easy addition of new repositories (just update REPOS in config.py)

Usage:
    python overall_summary_analysis.py

Or run the module directly:
    python -m summary_analysis

The module generates:
1. tests/deterministic/summary_analysis.json (aggregated data)
2. tests/deterministic/analysis_images/*.png and *.svg (7 visualizations)
3. tests/deterministic/analysis_images/analysis.md (comprehensive report)
"""

from summary_analysis.main import main

if __name__ == "__main__":
    main()
