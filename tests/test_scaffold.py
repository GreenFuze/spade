#!/usr/bin/env python3
"""
Test script for SPADE scaffold store functionality
Validates that scaffold store works correctly
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from logger import init_logger
from scaffold import ScaffoldStore
from schemas import NodeUpdate, HighLevelComponent, Evidence

# Initialize logger for tests
init_logger(Path("fakeapp"))


def test_initialization():
    """Test scaffold store initialization."""
    print("Testing scaffold store initialization...")

    repo_root = Path("fakeapp")

    # Clean up any existing scaffold files
    scaffold_dir = repo_root / ".spade" / "scaffold"
    if scaffold_dir.exists():
        import shutil

        shutil.rmtree(scaffold_dir)

    # Create workspace and store
    from workspace import Workspace

    workspace = Workspace(repo_root)
    store = ScaffoldStore(workspace)

    # Check that files were created
    if store.nodes_path.exists() and store.components_path.exists():
        print("✓ Scaffold files created successfully")
    else:
        print("✗ Scaffold files not created")
        return False

    # Check initial content
    nodes = store.load_nodes()
    components = store.load_components()

    if nodes == {} and components == []:
        print("✓ Initial content is correct (empty dict and list)")
    else:
        print(
            f"✗ Expected empty dict and list, got {type(nodes)} and {type(components)}"
        )
        return False

    return True


def test_merge_nodes():
    """Test node merging functionality."""
    print("\nTesting node merging...")

    repo_root = Path("fakeapp")
    from workspace import Workspace

    workspace = Workspace(repo_root)
    store = ScaffoldStore(workspace)

    # Create test NodeUpdate objects
    evidence1 = [Evidence(type="marker", value="Dockerfile")]
    evidence2 = [Evidence(type="lang_ext", value="py")]

    updates = {
        ".": NodeUpdate(
            summary="Root of the repository",
            languages=["python", "typescript"],
            tags=["root", "multi-language"],
            evidence=evidence1,
            confidence=0.9,
        ),
        "src": NodeUpdate(
            summary="Source code directory",
            languages=["python"],
            tags=["src", "code"],
            evidence=evidence2,
            confidence=0.8,
        ),
    }

    # Merge nodes
    store.merge_nodes(updates, step_id=1)

    # Check results
    nodes = store.load_nodes()

    if len(nodes) == 2:
        print("✓ Nodes merged successfully")
    else:
        print(f"✗ Expected 2 nodes, got {len(nodes)}")
        return False

    # Check specific node content
    root_node = nodes.get(".")
    if root_node and root_node.get("summary") == "Root of the repository":
        print("✓ Root node content correct")
    else:
        print("✗ Root node content incorrect")
        return False

    # Check that last_updated_step was set
    if root_node.get("last_updated_step") == 1:
        print("✓ last_updated_step set correctly")
    else:
        print("✗ last_updated_step not set correctly")
        return False

    return True


def test_merge_components():
    """Test component merging functionality."""
    print("\nTesting component merging...")

    repo_root = Path("fakeapp")
    from workspace import Workspace

    workspace = Workspace(repo_root)
    store = ScaffoldStore(workspace)

    # Create test HighLevelComponent objects
    evidence1 = [Evidence(type="marker", value="package.json")]
    evidence2 = [Evidence(type="name", value="api")]

    components = [
        HighLevelComponent(
            name="API Layer",
            role="Backend API",
            dirs=["src/api", "src/models"],
            evidence=evidence1,
            confidence=0.9,
        ),
        HighLevelComponent(
            name="Web Frontend",
            role="User Interface",
            dirs=["src/web", "src/ui"],
            evidence=evidence2,
            confidence=0.8,
        ),
    ]

    # Merge components
    store.merge_components(components)

    # Check results
    stored_components = store.load_components()

    if len(stored_components) == 2:
        print("✓ Components merged successfully")
    else:
        print(f"✗ Expected 2 components, got {len(stored_components)}")
        return False

    # Check specific component content
    api_component = next(
        (c for c in stored_components if c.get("name") == "API Layer"), None
    )
    if api_component and api_component.get("role") == "Backend API":
        print("✓ API component content correct")
    else:
        print("✗ API component content incorrect")
        return False

    return True


def test_component_deduplication():
    """Test component deduplication logic."""
    print("\nTesting component deduplication...")

    repo_root = Path("fakeapp")

    # Clean up any existing scaffold files
    scaffold_dir = repo_root / ".spade" / "scaffold"
    if scaffold_dir.exists():
        import shutil

        shutil.rmtree(scaffold_dir)

    from workspace import Workspace

    workspace = Workspace(repo_root)
    store = ScaffoldStore(workspace)

    # Create components with same name and dirs (should deduplicate)
    evidence1 = [Evidence(type="marker", value="Dockerfile")]
    evidence2 = [Evidence(type="name", value="api")]

    components1 = [
        HighLevelComponent(
            name="API Layer",
            role="Backend API",
            dirs=["src/api", "src/models"],
            evidence=evidence1,
            confidence=0.7,
        )
    ]

    components2 = [
        HighLevelComponent(
            name="API Layer",
            role="REST API Service",  # Different role
            dirs=["src/api", "src/models"],  # Same dirs
            evidence=evidence2,  # Different evidence
            confidence=0.9,  # Higher confidence
        )
    ]

    # Merge first set
    store.merge_components(components1)

    # Check initial count
    initial_components = store.load_components()
    if len(initial_components) == 1:
        print("✓ Initial component added")
    else:
        print(f"✗ Expected 1 component, got {len(initial_components)}")
        return False

    # Merge second set (should update existing)
    store.merge_components(components2)

    # Check final count (should still be 1 due to deduplication)
    final_components = store.load_components()
    if len(final_components) == 1:
        print("✓ Component deduplication worked")
    else:
        print(
            f"✗ Expected 1 component after deduplication, got {len(final_components)}"
        )
        return False

    # Check that the component was updated correctly
    updated_component = final_components[0]
    if (
        updated_component.get("role") == "REST API Service"  # Latest role
        and updated_component.get("confidence") == 0.9  # Max confidence
        and len(updated_component.get("evidence", [])) == 2
    ):  # Union of evidence
        print("✓ Component updated correctly (role, confidence, evidence)")
    else:
        print("✗ Component not updated correctly")
        return False

    return True


def test_ancestor_chain():
    """Test ancestor chain generation."""
    print("\nTesting ancestor chain generation...")

    repo_root = Path("fakeapp")
    from workspace import Workspace

    workspace = Workspace(repo_root)
    store = ScaffoldStore(workspace)

    # Add some test nodes
    updates = {
        ".": NodeUpdate(
            summary="Root repository",
            languages=["python"],
            tags=["root"],
            evidence=[],
            confidence=0.9,
        ),
        "src": NodeUpdate(
            summary="Source code",
            languages=["python", "typescript"],
            tags=["src", "code"],
            evidence=[],
            confidence=0.8,
        ),
        "src/api": NodeUpdate(
            summary="API layer",
            languages=["python"],
            tags=["api", "backend"],
            evidence=[],
            confidence=0.7,
        ),
    }

    store.merge_nodes(updates, step_id=1)

    # Test ancestor chain for "src/api/sub"
    chain = store.get_ancestor_chain("src/api/sub")

    expected_chain = [
        {"path": ".", "summary": "Root repository", "tags": ["root"]},
        {"path": "src", "summary": "Source code", "tags": ["src", "code"]},
    ]

    if chain == expected_chain:
        print("✓ Ancestor chain generated correctly")
    else:
        print(f"✗ Expected {expected_chain}, got {chain}")
        return False

    # Test ancestor chain for root (should be empty)
    root_chain = store.get_ancestor_chain(".")
    if root_chain == []:
        print("✓ Root ancestor chain is empty")
    else:
        print(f"✗ Expected empty chain for root, got {root_chain}")
        return False

    return True


def test_invalid_data_handling():
    """Test handling of invalid data."""
    print("\nTesting invalid data handling...")

    repo_root = Path("fakeapp")

    # Clean up any existing scaffold files
    scaffold_dir = repo_root / ".spade" / "scaffold"
    if scaffold_dir.exists():
        import shutil

        shutil.rmtree(scaffold_dir)

    from workspace import Workspace

    workspace = Workspace(repo_root)
    store = ScaffoldStore(workspace)

    # Test invalid NodeUpdate
    invalid_updates = {"invalid": {"invalid": "data"}}  # Not a NodeUpdate

    # This should not crash and should skip invalid entries
    store.merge_nodes(invalid_updates, step_id=1)

    nodes = store.load_nodes()
    if "invalid" not in nodes:
        print("✓ Invalid NodeUpdate skipped correctly")
    else:
        print("✗ Invalid NodeUpdate was not skipped")
        return False

    # Test invalid HighLevelComponent
    invalid_components = [{"invalid": "component"}]  # Not a HighLevelComponent

    # This should not crash and should skip invalid entries
    store.merge_components(invalid_components)

    components = store.load_components()
    if len(components) == 0:
        print("✓ Invalid HighLevelComponent skipped correctly")
    else:
        print("✗ Invalid HighLevelComponent was not skipped")
        return False

    return True


def test_acceptance_criteria():
    """Test the exact acceptance criteria."""
    print("\nTesting acceptance criteria...")

    repo_root = Path("fakeapp")

    # Clean up and create fresh store
    scaffold_dir = repo_root / ".spade" / "scaffold"
    if scaffold_dir.exists():
        import shutil

        shutil.rmtree(scaffold_dir)

    from workspace import Workspace

    workspace = Workspace(repo_root)
    store = ScaffoldStore(workspace)

    # Test 1: Files created with correct initial content
    if (
        store.nodes_path.exists()
        and store.components_path.exists()
        and store.load_nodes() == {}
        and store.load_components() == []
    ):
        print("✓ Files created with correct initial content")
    else:
        print("✗ Files not created with correct initial content")
        return False

    # Test 2: merge_nodes upserts paths and sets last_updated_step
    updates = {
        "test": NodeUpdate(
            summary="Test node",
            languages=["python"],
            tags=["test"],
            evidence=[],
            confidence=0.8,
        )
    }

    store.merge_nodes(updates, step_id=5)
    nodes = store.load_nodes()

    if (
        "test" in nodes
        and nodes["test"]["last_updated_step"] == 5
        and nodes["test"]["summary"] == "Test node"
    ):
        print("✓ merge_nodes upserts paths and sets last_updated_step")
    else:
        print("✗ merge_nodes does not work correctly")
        return False

    # Test 3: merge_components deduplicates and unions evidence
    comp1 = HighLevelComponent(
        name="Test Component",
        role="Test Role",
        dirs=["dir1", "dir2"],
        evidence=[Evidence(type="marker", value="test1")],
        confidence=0.7,
    )

    comp2 = HighLevelComponent(
        name="Test Component",
        role="Updated Role",
        dirs=["dir1", "dir2"],  # Same dirs
        evidence=[Evidence(type="marker", value="test2")],  # Different evidence
        confidence=0.9,  # Higher confidence
    )

    store.merge_components([comp1])
    store.merge_components([comp2])

    components = store.load_components()
    if (
        len(components) == 1  # Deduplicated
        and components[0]["role"] == "Updated Role"  # Latest role
        and components[0]["confidence"] == 0.9  # Max confidence
        and len(components[0]["evidence"]) == 2
    ):  # Union of evidence
        print("✓ merge_components deduplicates and unions evidence")
    else:
        print("✗ merge_components does not work correctly")
        return False

    # Test 4: get_ancestor_chain returns correct structure
    chain = store.get_ancestor_chain("a/b/c")
    if (
        isinstance(chain, list)
        and len(chain) == 2
        and chain[0]["path"] == "."
        and chain[1]["path"] == "a"
    ):
        print("✓ get_ancestor_chain returns correct structure")
    else:
        print("✗ get_ancestor_chain does not work correctly")
        return False

    print("✓ All acceptance criteria met")
    return True


def main():
    """Run all tests."""
    print("SPADE Scaffold Store Test Suite")
    print("=" * 50)

    try:
        success1 = test_initialization()
        success2 = test_merge_nodes()
        success3 = test_merge_components()
        success4 = test_component_deduplication()
        success5 = test_ancestor_chain()
        success6 = test_invalid_data_handling()
        success7 = test_acceptance_criteria()

        if (
            success1
            and success2
            and success3
            and success4
            and success5
            and success6
            and success7
        ):
            print("\n" + "=" * 50)
            print("✓ All tests passed! Scaffold store working correctly.")
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
