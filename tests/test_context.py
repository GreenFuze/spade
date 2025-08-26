#!/usr/bin/env python3
"""
Test script for SPADE Phase-0 context builder functionality
Validates that context building works correctly
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from context import (
    _load_nodes_scaffold, _ancestor_chain, build_ancestors, 
    build_phase0_context, pretty_json
)
from snapshot import build_snapshot, enrich_markers_and_samples, compute_deterministic_scoring
from workspace import Workspace


def test_ancestor_chain():
    """Test ancestor chain generation."""
    print("Testing ancestor chain generation...")
    
    # Test cases
    test_cases = [
        (".", []),
        ("api", ["."]),
        ("web/subdir", [".", "web"]),
        ("a/b/c", [".", "a", "a/b"]),
        ("single", ["."]),
        ("deep/nested/path", [".", "deep", "deep/nested"])
    ]
    
    for rel, expected in test_cases:
        result = _ancestor_chain(rel)
        if result == expected:
            print(f"✓ {rel} -> {result}")
        else:
            print(f"✗ {rel} -> expected {expected}, got {result}")
            return False
    
    return True


def test_load_nodes_scaffold():
    """Test scaffold loading functionality."""
    print("\nTesting scaffold loading...")
    
    repo_root = Path("fakeapp")
    scaffold_path = repo_root / ".spade" / "scaffold" / "repository_scaffold.json"
    
    # Ensure no scaffold file exists initially
    if scaffold_path.exists():
        scaffold_path.unlink()
    
    # Test when file doesn't exist
    nodes = _load_nodes_scaffold(repo_root)
    if nodes == {}:
        print("✓ Empty dict when scaffold file doesn't exist")
    else:
        print(f"✗ Expected empty dict, got: {nodes}")
        return False
    
    # Create a test scaffold file
    scaffold_data = {
        ".": {"summary": "repo summary", "tags": ["python"]},
        "api": {"summary": "API layer", "tags": ["api", "python"]},
        "web": {"summary": "Web frontend", "tags": ["web", "javascript"]}
    }
    
    scaffold_path.parent.mkdir(exist_ok=True)
    with open(scaffold_path, 'w') as f:
        json.dump(scaffold_data, f)
    
    # Test loading the file
    loaded = _load_nodes_scaffold(repo_root)
    if loaded == scaffold_data:
        print("✓ Scaffold file loaded correctly")
    else:
        print(f"✗ Expected {scaffold_data}, got {loaded}")
        # Clean up before returning
        if scaffold_path.exists():
            scaffold_path.unlink()
        return False
    
    # Clean up
    scaffold_path.unlink()
    
    return True


def test_build_ancestors():
    """Test ancestor building functionality."""
    print("\nTesting ancestor building...")
    
    repo_root = Path("fakeapp")
    scaffold_path = repo_root / ".spade" / "scaffold" / "repository_scaffold.json"
    
    # Ensure no scaffold file exists initially
    if scaffold_path.exists():
        scaffold_path.unlink()
    
    # Test without scaffold file
    ancestors = build_ancestors(repo_root, "api/sub")
    if ancestors == []:
        print("✓ Empty ancestors when no scaffold file exists")
    else:
        print(f"✗ Expected empty list, got: {ancestors}")
        return False
    
    # Create scaffold file and test
    scaffold_data = {
        ".": {"summary": "repo summary", "tags": ["python"]},
        "api": {"summary": "API layer", "tags": ["api", "python"]}
    }
    
    scaffold_path.parent.mkdir(exist_ok=True)
    with open(scaffold_path, 'w') as f:
        json.dump(scaffold_data, f)
    
    # Test building ancestors for "api/sub"
    ancestors = build_ancestors(repo_root, "api/sub")
    expected = [
        {"path": ".", "summary": "repo summary", "tags": ["python"]},
        {"path": "api", "summary": "API layer", "tags": ["api", "python"]}
    ]
    
    if ancestors == expected:
        print("✓ Ancestors built correctly with scaffold data")
    else:
        print(f"✗ Expected {expected}, got {ancestors}")
        # Clean up before returning
        if scaffold_path.exists():
            scaffold_path.unlink()
        return False
    
    # Clean up
    scaffold_path.unlink()
    
    return True


def test_build_phase0_context():
    """Test full context building functionality."""
    print("\nTesting build_phase0_context...")
    
    repo_root = Path("fakeapp")
    config = Workspace.load_config(repo_root)
    
    # Build snapshot and enrich with markers and scoring first
    print("Building snapshot and enriching with markers and scoring...")
    build_snapshot(repo_root, config)
    enrich_markers_and_samples(repo_root, config)
    compute_deterministic_scoring(repo_root, config)
    
    # Test building context for root directory
    try:
        context = build_phase0_context(repo_root, ".", config)
        
        # Check required fields
        required_fields = ["repo_root_name", "ancestors", "current", "siblings", "excluded_children", "deterministic_scoring"]
        for field in required_fields:
            if field not in context:
                print(f"✗ Missing required field: {field}")
                return False
        
        # Check specific structure
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
        
        print("✓ Context structure is valid")
        print(f"  repo_root_name: {context['repo_root_name']}")
        print(f"  ancestors: {len(context['ancestors'])} items")
        print(f"  siblings: {len(context['siblings'])} items")
        print(f"  excluded_children: {len(context['excluded_children'])} items")
        print(f"  deterministic_scoring children: {len(context['deterministic_scoring']['children'])} items")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to build context: {e}")
        return False


def test_context_with_scaffold():
    """Test context building with scaffold data."""
    print("\nTesting context with scaffold data...")
    
    repo_root = Path("fakeapp")
    config = Workspace.load_config(repo_root)
    
    # Create scaffold file
    scaffold_data = {
        ".": {"summary": "Multi-language application", "tags": ["python", "typescript"]},
        "api": {"summary": "API layer", "tags": ["api", "python"]},
        "web": {"summary": "Web frontend", "tags": ["web", "javascript"]}
    }
    
    scaffold_path = repo_root / ".spade" / "scaffold" / "repository_scaffold.json"
    scaffold_path.parent.mkdir(exist_ok=True)
    with open(scaffold_path, 'w') as f:
        json.dump(scaffold_data, f)
    
    try:
        # Test context for "src" directory (which exists in fakeapp)
        context = build_phase0_context(repo_root, "src", config)
        
        # Check ancestors
        ancestors = context["ancestors"]
        if len(ancestors) == 1 and ancestors[0]["path"] == ".":
            print("✓ Ancestors correctly built for 'src' directory")
        else:
            print(f"✗ Expected 1 ancestor for 'src', got: {ancestors}")
            return False
        
        # Test context for "src/api" (should have 2 ancestors)
        context = build_phase0_context(repo_root, "src/api", config)
        ancestors = context["ancestors"]
        if len(ancestors) == 2 and ancestors[0]["path"] == "." and ancestors[1]["path"] == "src":
            print("✓ Ancestors correctly built for 'src/api' directory")
        else:
            print(f"✗ Expected 2 ancestors for 'src/api', got: {ancestors}")
            return False
        
        # Clean up
        scaffold_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to build context with scaffold: {e}")
        # Clean up
        if scaffold_path.exists():
            scaffold_path.unlink()
        return False


def test_context_acceptance():
    """Test the exact acceptance criteria."""
    print("\nTesting acceptance criteria...")
    
    repo_root = Path("fakeapp")
    config = Workspace.load_config(repo_root)
    
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
        context = build_phase0_context(repo_root, "src/api", config)
        
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
        
        print("✓ Acceptance criteria met: context matches exact schema")
        
        # Show sample of the context structure
        print("\nSample context structure:")
        print(f"  repo_root_name: {context['repo_root_name']}")
        print(f"  ancestors: {len(context['ancestors'])} items")
        print(f"  siblings: {context['siblings']}")
        print(f"  excluded_children: {context['excluded_children']}")
        print(f"  deterministic_scoring: {context['deterministic_scoring']}")
        
        # Clean up
        scaffold_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to test acceptance criteria: {e}")
        # Clean up
        if scaffold_path.exists():
            scaffold_path.unlink()
        return False


def main():
    """Run all tests."""
    print("SPADE Phase-0 Context Builder Test Suite")
    print("=" * 50)
    
    try:
        success1 = test_ancestor_chain()
        success2 = test_load_nodes_scaffold()
        success3 = test_build_ancestors()
        success4 = test_build_phase0_context()
        success5 = test_context_with_scaffold()
        success6 = test_context_acceptance()
        
        if success1 and success2 and success3 and success4 and success5 and success6:
            print("\n" + "=" * 50)
            print("✓ All tests passed! Phase-0 context builder working correctly.")
        else:
            print("\n" + "=" * 50)
            print("✗ Some tests failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
