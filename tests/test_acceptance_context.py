#!/usr/bin/env python3
"""
Test acceptance criteria for Phase-0 context builder
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from context import build_phase0_context, pretty_json
from snapshot import build_snapshot, enrich_markers_and_samples, compute_deterministic_scoring
from workspace import Workspace

def test_acceptance_criteria():
    """Test the exact acceptance criteria from the task."""
    print("Testing context builder acceptance criteria...")
    
    repo_root = Path("fakeapp")
    cfg = Workspace.load_config(repo_root)
    
    # Run the full pipeline
    print("Running full pipeline: snapshot + markers + scoring...")
    build_snapshot(repo_root, cfg)
    enrich_markers_and_samples(repo_root, cfg)
    compute_deterministic_scoring(repo_root, cfg)
    
    # Create scaffold file with the exact example from acceptance criteria
    scaffold_data = {
        ".": {"summary": "repo summary", "tags": ["python"]},
        "src": {"summary": "Source code", "tags": ["src", "python"]}
    }
    
    scaffold_path = repo_root / ".spade" / "scaffold" / "repository_scaffold.json"
    scaffold_path.parent.mkdir(exist_ok=True)
    with open(scaffold_path, 'w') as f:
        json.dump(scaffold_data, f)
    
    try:
        # Test the exact example: build_phase0_context(repo_root, "src/api", cfg)
        context = build_phase0_context(repo_root, "src/api", cfg)
        
        # Check ancestors match the expected format
        ancestors = context["ancestors"]
        expected_ancestors = [
            {"path": ".", "summary": "repo summary", "tags": ["python"]},
            {"path": "src", "summary": "Source code", "tags": ["src", "python"]}
        ]
        
        if ancestors == expected_ancestors:
            print("✓ Ancestors match acceptance criteria exactly")
            print(f"  ancestors: {ancestors}")
        else:
            print(f"✗ Expected {expected_ancestors}, got {ancestors}")
            return False
        
        # Check overall schema
        required_fields = ["repo_root_name", "ancestors", "current", "siblings", "excluded_children", "deterministic_scoring"]
        for field in required_fields:
            if field not in context:
                print(f"✗ Missing required field: {field}")
                return False
        
        # Check specific field types
        if not isinstance(context["repo_root_name"], str):
            print("✗ repo_root_name should be string")
            return False
        
        if not isinstance(context["ancestors"], list):
            print("✗ ancestors should be list")
            return False
        
        if not isinstance(context["current"], dict):
            print("✗ current should be dict")
            return False
        
        if not isinstance(context["siblings"], list):
            print("✗ siblings should be list")
            return False
        
        if not isinstance(context["excluded_children"], list):
            print("✗ excluded_children should be list")
            return False
        
        if not isinstance(context["deterministic_scoring"], dict):
            print("✗ deterministic_scoring should be dict")
            return False
        
        if "children" not in context["deterministic_scoring"]:
            print("✗ deterministic_scoring should have 'children' key")
            return False
        
        # Check that current doesn't contain the extracted fields
        extracted_fields = ["siblings", "excluded_children", "deterministic_scoring"]
        for field in extracted_fields:
            if field in context["current"]:
                print(f"✗ current should not contain {field}")
                return False
        
        print("✓ Acceptance criteria met: context matches exact schema")
        
        # Show the complete context structure
        print("\nComplete context structure:")
        print(pretty_json(context))
        
        # Clean up
        scaffold_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to test acceptance criteria: {e}")
        # Clean up
        if scaffold_path.exists():
            scaffold_path.unlink()
        return False

if __name__ == "__main__":
    test_acceptance_criteria()
