"""
ResearchBackedUtilities class for research-backed upgrades to maximize coverage before falling back to UNKNOWN.
Implements evidence-first approach with no heuristics.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

