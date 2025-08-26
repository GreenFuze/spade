#!/usr/bin/env python3
"""
Test acceptance criteria for language mapping
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from languages import active_map, aggregate_languages
from workspace import Workspace

def test_acceptance_criteria():
    """Test the exact acceptance criteria from the task."""
    print("Testing acceptance criteria...")
    
    repo_root = Path("fakeapp")
    cfg = Workspace.load_config(repo_root)
    
    # Test active_map
    mapping = active_map(cfg, repo_root)
    print(f"✓ active_map returned {len(mapping)} mappings")
    
    # Test aggregate_languages with the exact example from acceptance criteria
    ext_histogram = {"py": 10, "ts": 3, "md": 7, ".env": 2}
    ext2lang = {"py": "python", "ts": "typescript"}
    
    result = aggregate_languages(ext_histogram, ext2lang)
    expected = [("python", 10), ("typescript", 3)]
    
    if result == expected:
        print("✓ aggregate_languages works exactly as specified in acceptance criteria")
        print(f"  Input: {ext_histogram}")
        print(f"  Output: {result}")
    else:
        print(f"✗ Expected {expected}, got {result}")
        return False
    
    return True

if __name__ == "__main__":
    test_acceptance_criteria()
