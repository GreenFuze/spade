"""
Configuration module for RIG effectiveness summary analysis.

This module contains all configuration constants used throughout the analysis:
- Repository paths
- Visualization colors
- Agent display names
- Complexity calculation weights

All values are defined here to ensure single source of truth and easy updates.
"""

from pathlib import Path

# Base directory for the analysis
SCRIPT_DIR = Path(__file__).parent.parent

# Repository configuration
# IMPORTANT: This is the single source of truth for repositories to analyze
# To add a new repository, simply add it to this list with name and path
REPOS = [
    {
        "name": "cmake_hello_world",
        "path": SCRIPT_DIR / "cmake" / "cmake_hello_world",
    },
    {
        "name": "jni_hello_world",
        "path": SCRIPT_DIR / "cmake" / "jni_hello_world",
    },
    {
        "name": "metaffi",
        "path": SCRIPT_DIR / "cmake" / "metaffi",
    },
]

# Visualization color scheme (colorblind-friendly)
COLORS = {
    'without_rig': '#E74C3C',  # Red
    'with_rig': '#27AE60',     # Green
    'claude': '#3498DB',        # Blue
    'codex': '#9B59B6',        # Purple
    'cursor': '#F39C12',       # Orange
    'positive': '#27AE60',     # Green
    'negative': '#E74C3C',     # Red
    'neutral': '#95A5A6',      # Gray
}

# Marker shapes for agents (prevents overlapping points from being invisible)
MARKERS = {
    'claude': 'o',   # Circle
    'codex': 's',    # Square
    'cursor': '^',   # Triangle
}

# Agent display names
AGENT_DISPLAY = {
    'claude': 'Claude',
    'codex': 'Codex',
    'cursor': 'Cursor',
}

# Question difficulty levels
DIFFICULTIES = ['easy', 'medium', 'hard']

DIFFICULTY_DISPLAY = {
    'easy': 'Easy',
    'medium': 'Medium',
    'hard': 'Hard',
}

# Complexity calculation weights
# These weights determine how each metric contributes to the overall complexity score
COMPLEXITY_WEIGHTS = {
    'component': 2,           # Weight for component count
    'language': 10,           # Weight for programming language count (highest weight)
    'package': 3,             # Weight for external package count
    'depth': 8,               # Weight for max dependency depth
    'aggregator': 5,          # Weight for aggregator count
    'cross_lang_bonus': 15,   # Bonus for cross-language dependencies
}

# Complexity level thresholds (for categorization)
COMPLEXITY_THRESHOLDS = {
    'low': 30,     # Score < 30 → LOW
    'medium': 70,  # 30 <= Score < 70 → MEDIUM
    # Score >= 70 → HIGH
}

# Matplotlib style configuration for academic papers
PLOT_STYLE = 'seaborn-v0_8-paper'
PLOT_DPI = 300
PLOT_FONT_SIZE = 10
PLOT_FONT_FAMILY = 'serif'
PLOT_AXES_LABELSIZE = 12
PLOT_AXES_TITLESIZE = 14
PLOT_LEGEND_FONTSIZE = 10
PLOT_TICK_LABELSIZE = 10
PLOT_FIGURE_SIZE = (10, 8)  # Default size for most charts
