#!/usr/bin/env python3
"""
Test script for SPADE marker detection functionality
Validates that marker detection and sample enrichment works correctly
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from markers import SEED_MARKERS, load_learned_markers, active_rules, detect_markers_for_dir
from snapshot import build_snapshot, enrich_markers_and_samples
from workspace import Workspace
from schemas import load_json, DirMeta


def test_seed_markers():
    """Test that seed markers are properly defined."""
    print("Testing seed markers...")
    
    # Check that all seed markers have required fields
    required_fields = ["match", "type", "weight"]
    for i, marker in enumerate(SEED_MARKERS):
        for field in required_fields:
            if field not in marker:
                print(f"✗ Seed marker {i} missing required field: {field}")
                return False
    
    print(f"✓ {len(SEED_MARKERS)} seed markers loaded with required fields")
    return True


def test_marker_detection():
    """Test marker detection on fakeapp repository."""
    print("\nTesting marker detection...")
    
    repo_root = Path("fakeapp")
    
    # Test detection on root directory
    rules = active_rules(Workspace.load_config(repo_root), repo_root)
    markers = detect_markers_for_dir(repo_root, rules)
    
    print(f"✓ Root directory markers: {markers}")
    
    # Test detection on .github directory
    github_dir = repo_root / ".github"
    if github_dir.exists():
        github_markers = detect_markers_for_dir(github_dir, rules)
        print(f"✓ .github directory markers: {github_markers}")
    
    # Test detection on src directory
    src_dir = repo_root / "src"
    if src_dir.exists():
        src_markers = detect_markers_for_dir(src_dir, rules)
        print(f"✓ src directory markers: {src_markers}")
    
    return True


def test_sample_priority():
    """Test that samples prioritize markers correctly."""
    print("\nTesting sample priority...")
    
    repo_root = Path("fakeapp")
    config = Workspace.load_config(repo_root)
    
    # Build snapshot first
    print("Building snapshot...")
    build_snapshot(repo_root, config)
    
    # Then enrich with markers
    print("Enriching with markers...")
    enrich_markers_and_samples(repo_root, config)
    
    # Check root dirmeta
    root_dirmeta_path = repo_root / ".spade" / "snapshot" / "dirmeta.json"
    if root_dirmeta_path.exists():
        root_dirmeta = load_json(root_dirmeta_path, DirMeta)
        print(f"✓ Root markers: {root_dirmeta.markers}")
        print(f"✓ Root sample dirs: {root_dirmeta.samples.dirs}")
        print(f"✓ Root sample files: {root_dirmeta.samples.files}")
        
        # Check that markers appear first in samples if they exist
        if root_dirmeta.markers:
            for marker in root_dirmeta.markers:
                if '/' in marker:
                    # Path pattern - check if basename is in samples
                    basename = marker.split('/')[-1]
                    if basename in root_dirmeta.samples.dirs:
                        print(f"✓ Path marker '{marker}' basename '{basename}' found in sample dirs")
                else:
                    # Direct name - check if it's in samples
                    if marker in root_dirmeta.samples.files:
                        print(f"✓ File marker '{marker}' found in sample files")
                    elif marker in root_dirmeta.samples.dirs:
                        print(f"✓ Dir marker '{marker}' found in sample dirs")
    
    # Check .github dirmeta
    github_dirmeta_path = repo_root / ".spade" / "snapshot" / ".github" / "dirmeta.json"
    if github_dirmeta_path.exists():
        github_dirmeta = load_json(github_dirmeta_path, DirMeta)
        print(f"✓ .github markers: {github_dirmeta.markers}")
        print(f"✓ .github sample dirs: {github_dirmeta.samples.dirs}")
        print(f"✓ .github sample files: {github_dirmeta.samples.files}")
    
    return True


def test_learned_markers():
    """Test learned markers functionality."""
    print("\nTesting learned markers...")
    
    repo_root = Path("fakeapp")
    
    # Test loading when file doesn't exist
    learned = load_learned_markers(repo_root)
    if learned == []:
        print("✓ Empty learned markers when file doesn't exist")
    else:
        print(f"✗ Expected empty list, got: {learned}")
        return False
    
    # Create a test learned markers file
    learned_markers = [
        {"match": "custom.config", "type": "config", "weight": 0.5},
        {"match": "special.file", "type": "special", "weight": 0.8}
    ]
    
    learned_path = repo_root / ".spade" / "markers.learned.json"
    learned_path.parent.mkdir(exist_ok=True)
    with open(learned_path, 'w') as f:
        json.dump(learned_markers, f)
    
    # Test loading the file
    loaded = load_learned_markers(repo_root)
    if loaded == learned_markers:
        print("✓ Learned markers loaded correctly")
    else:
        print(f"✗ Expected {learned_markers}, got {loaded}")
        return False
    
    # Clean up
    learned_path.unlink()
    
    return True


def test_marker_rules():
    """Test marker rule matching logic."""
    print("\nTesting marker rule matching...")
    
    # Test simple name matching
    test_rules = [
        {"match": "package.json", "type": "build", "weight": 0.8},
        {"match": "Dockerfile", "type": "deploy", "weight": 0.7},
        {"match": ".github/workflows/", "type": "ci", "weight": 0.6}
    ]
    
    # Create a test directory with some files
    test_dir = Path("test_markers")
    test_dir.mkdir(exist_ok=True)
    
    # Create test files
    (test_dir / "package.json").touch()
    (test_dir / "Dockerfile").touch()
    (test_dir / ".github").mkdir(exist_ok=True)
    (test_dir / ".github" / "workflows").mkdir(exist_ok=True)
    (test_dir / ".github" / "workflows" / "test.yml").touch()
    
    # Test detection
    markers = detect_markers_for_dir(test_dir, test_rules)
    expected = ["Dockerfile", "package.json", ".github/workflows/"]
    
    if set(markers) == set(expected):
        print("✓ Marker detection works correctly")
    else:
        print(f"✗ Expected {expected}, got {markers}")
        return False
    
    # Clean up
    import shutil
    shutil.rmtree(test_dir)
    
    return True


def main():
    """Run all tests."""
    print("SPADE Marker Detection Test Suite")
    print("=" * 50)
    
    try:
        success1 = test_seed_markers()
        success2 = test_marker_detection()
        success3 = test_sample_priority()
        success4 = test_learned_markers()
        success5 = test_marker_rules()
        
        if success1 and success2 and success3 and success4 and success5:
            print("\n" + "=" * 50)
            print("✓ All tests passed! Marker detection working correctly.")
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
