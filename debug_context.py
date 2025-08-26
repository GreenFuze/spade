#!/usr/bin/env python3
"""
Debug script for context builder test
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from context import build_ancestors

def debug_build_ancestors():
    """Debug the build_ancestors function."""
    print("Debugging build_ancestors...")
    
    repo_root = Path("fakeapp")
    scaffold_path = repo_root / ".spade" / "scaffold" / "repository_scaffold.json"
    
    print(f"Scaffold path: {scaffold_path}")
    print(f"Scaffold exists: {scaffold_path.exists()}")
    
    if scaffold_path.exists():
        print(f"Scaffold content: {scaffold_path.read_text()}")
    
    # Test without scaffold file
    ancestors = build_ancestors(repo_root, "api/sub")
    print(f"Ancestors result: {ancestors}")
    
    if ancestors == []:
        print("✓ Empty ancestors when no scaffold file exists")
    else:
        print(f"✗ Expected empty list, got: {ancestors}")

if __name__ == "__main__":
    debug_build_ancestors()
