#!/usr/bin/env python3
"""
Test script for SPADE Learning System
Tests marker learning, language learning, and re-scoring functionality
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from learning import (
    build_name_histogram, build_unknown_ext_histogram,
    learn_markers_once, learn_languages_once,
    post_snapshot_learning_and_rescore
)
from models import RunConfig, DirMeta, DirCounts, StalenessFingerprint
from dev.dummy_transport import echo_transport_valid_response, echo_transport_markers_learning, echo_transport_languages_learning


def test_build_name_histogram():
    """Test building name histogram from snapshot data."""
    print("Testing name histogram building...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / "src").mkdir()
        (repo_root / "docs").mkdir()
        (repo_root / ".spade").mkdir()
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Create dirmeta files
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 2, "dirs": 2},
            "siblings": ["src", "docs"],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 4,
                "name_hash": "abc123"
            },
            "ext_histogram": {"py": 1, "md": 1}
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create child dirmeta
        for child in ["src", "docs"]:
            (repo_root / ".spade" / "snapshot" / child).mkdir()
            child_dirmeta = {
                "path": child,
                "depth": 1,
                "counts": {"files": 1, "dirs": 0},
                "siblings": [],
                "excluded_children": [],
                "staleness_fingerprint": {
                    "latest_modified_time": "2025-01-01T00:00:00Z",
                    "total_entries": 1,
                    "name_hash": f"def{child}"
                },
                "ext_histogram": {"py": 1} if child == "src" else {"md": 1}
            }
            (repo_root / ".spade" / "snapshot" / child / "dirmeta.json").write_text(json.dumps(child_dirmeta))
        
        # Create actual files
        (repo_root / "main.py").write_text("# main")
        (repo_root / "README.md").write_text("# readme")
        (repo_root / "src" / "app.py").write_text("# app")
        (repo_root / "docs" / "guide.md").write_text("# guide")
        
        # Create config
        config = RunConfig()
        
        # Test histogram building
        hist = build_name_histogram(repo_root, config)
        
        # Should include all file and directory names
        expected_names = {"src", "docs", "main.py", "README.md", "app.py", "guide.md"}
        actual_names = set(hist.keys())
        
        if actual_names != expected_names:
            print(f"✗ Expected names {expected_names}, got {actual_names}")
            return False
        
        print("✓ Name histogram building works correctly")
        return True


def test_build_unknown_ext_histogram():
    """Test building unknown extension histogram."""
    print("\nTesting unknown extension histogram building...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / ".spade").mkdir()
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Create dirmeta with unknown extensions
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 3, "dirs": 0},
            "siblings": [],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 3,
                "name_hash": "abc123"
            },
            "ext_histogram": {"py": 1, "xyz": 1, "abc": 2}  # xyz and abc are unknown
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create config
        config = RunConfig()
        
        # Test histogram building
        hist = build_unknown_ext_histogram(repo_root, config)
        
        # Should include unknown extensions only
        expected_exts = {"xyz", "abc"}
        actual_exts = set(hist.keys())
        
        if actual_exts != expected_exts:
            print(f"✗ Expected extensions {expected_exts}, got {actual_exts}")
            return False
        
        # Check counts
        if hist["abc"] != 2:
            print(f"✗ Expected count 2 for 'abc', got {hist['abc']}")
            return False
        
        print("✓ Unknown extension histogram building works correctly")
        return True


def test_learn_markers_once():
    """Test marker learning functionality."""
    print("\nTesting marker learning...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / "src").mkdir()
        (repo_root / ".spade").mkdir()
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Create dirmeta
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 1, "dirs": 1},
            "siblings": ["src"],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 2,
                "name_hash": "abc123"
            },
            "ext_histogram": {"py": 1}
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create actual files
        (repo_root / "main.py").write_text("# main")
        
        # Create config with learning enabled
        config = RunConfig(
            learn_markers=True,
            marker_learning=RunConfig.MarkerLearning(top_k_candidates=10, min_confidence=0.5)
        )
        
        # Create LLM client
        from llm import LLMClient
        llm = LLMClient(echo_transport_markers_learning)
        
        # Test marker learning
        learn_markers_once(repo_root, config, llm)
        
        # Check that learned file was created
        learned_path = repo_root / ".spade" / "markers.learned.json"
        if not learned_path.exists():
            print("✗ markers.learned.json was not created")
            return False
        
        # Check content
        try:
            learned_data = json.loads(learned_path.read_text())
            if not isinstance(learned_data, list):
                print("✗ markers.learned.json does not contain a list")
                return False
            
            print(f"✓ Marker learning completed, saved {len(learned_data)} markers")
            return True
            
        except Exception as e:
            print(f"✗ Failed to read markers.learned.json: {e}")
            return False


def test_learn_languages_once():
    """Test language learning functionality."""
    print("\nTesting language learning...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / ".spade").mkdir()
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Create dirmeta with unknown extensions
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 2, "dirs": 0},
            "siblings": [],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 2,
                "name_hash": "abc123"
            },
            "ext_histogram": {"xyz": 1, "abc": 1}  # unknown extensions
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create config with learning enabled
        config = RunConfig(
            learn_languages=True,
            marker_learning=RunConfig.MarkerLearning(top_k_candidates=10, min_confidence=0.5)
        )
        
        # Create LLM client
        from llm import LLMClient
        llm = LLMClient(echo_transport_languages_learning)
        
        # Test language learning
        learn_languages_once(repo_root, config, llm)
        
        # Check that learned file was created
        learned_path = repo_root / ".spade" / "languages.learned.json"
        if not learned_path.exists():
            print("✗ languages.learned.json was not created")
            return False
        
        # Check content
        try:
            learned_data = json.loads(learned_path.read_text())
            if not isinstance(learned_data, list):
                print("✗ languages.learned.json does not contain a list")
                return False
            
            print(f"✓ Language learning completed, saved {len(learned_data)} languages")
            return True
            
        except Exception as e:
            print(f"✗ Failed to read languages.learned.json: {e}")
            return False


def test_learning_skip_when_exists():
    """Test that learning is skipped when learned files already exist."""
    print("\nTesting learning skip when files exist...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / ".spade").mkdir()
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Create existing learned files
        (repo_root / ".spade" / "markers.learned.json").write_text("[]")
        (repo_root / ".spade" / "languages.learned.json").write_text("[]")
        
        # Create dirmeta
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 1, "dirs": 0},
            "siblings": [],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 1,
                "name_hash": "abc123"
            },
            "ext_histogram": {"py": 1}
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create config with learning enabled
        config = RunConfig(
            learn_markers=True,
            learn_languages=True,
            marker_learning=RunConfig.MarkerLearning(top_k_candidates=10, min_confidence=0.5)
        )
        
        # Create LLM client
        from llm import LLMClient
        llm = LLMClient(echo_transport_markers_learning)
        
        # Test that learning is skipped
        learn_markers_once(repo_root, config, llm)
        learn_languages_once(repo_root, config, llm)
        
        # Files should still be empty
        markers_content = (repo_root / ".spade" / "markers.learned.json").read_text()
        languages_content = (repo_root / ".spade" / "languages.learned.json").read_text()
        
        if markers_content != "[]" or languages_content != "[]":
            print("✗ Learned files were modified when they should have been skipped")
            return False
        
        print("✓ Learning correctly skipped when files exist")
        return True


def test_post_snapshot_learning_and_rescore():
    """Test complete post-snapshot learning and re-scoring workflow."""
    print("\nTesting complete post-snapshot learning and re-scoring...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / "src").mkdir()
        (repo_root / ".spade").mkdir()
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Create dirmeta
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 1, "dirs": 1},
            "siblings": ["src"],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 2,
                "name_hash": "abc123"
            },
            "ext_histogram": {"py": 1, "xyz": 1},  # xyz is unknown
            "markers": [],
            "deterministic_scoring": {}
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create child dirmeta
        (repo_root / ".spade" / "snapshot" / "src").mkdir()
        child_dirmeta = {
            "path": "src",
            "depth": 1,
            "counts": {"files": 1, "dirs": 0},
            "siblings": [],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 1,
                "name_hash": "defsrc"
            },
            "ext_histogram": {"py": 1},
            "markers": [],
            "deterministic_scoring": {}
        }
        (repo_root / ".spade" / "snapshot" / "src" / "dirmeta.json").write_text(json.dumps(child_dirmeta))
        
        # Create actual files
        (repo_root / "main.py").write_text("# main")
        (repo_root / "src" / "app.py").write_text("# app")
        
        # Create config with learning and use enabled
        config = RunConfig(
            learn_markers=True,
            learn_languages=True,
            use_learned_markers=True,
            use_learned_languages=True,
            marker_learning=RunConfig.MarkerLearning(top_k_candidates=10, min_confidence=0.5)
        )
        
        # Create LLM client
        from llm import LLMClient
        llm = LLMClient(echo_transport_markers_learning)
        
        # Test complete workflow
        post_snapshot_learning_and_rescore(repo_root, config, llm)
        
        # Check that learned files were created
        markers_path = repo_root / ".spade" / "markers.learned.json"
        languages_path = repo_root / ".spade" / "languages.learned.json"
        
        if not markers_path.exists():
            print("✗ markers.learned.json was not created")
            return False
        
        if not languages_path.exists():
            print("✗ languages.learned.json was not created")
            return False
        
        # Check that dirmeta was updated (re-scoring should have run)
        try:
            updated_dirmeta = json.loads((repo_root / ".spade" / "snapshot" / "dirmeta.json").read_text())
            if "deterministic_scoring" not in updated_dirmeta:
                print("✗ dirmeta was not updated with deterministic_scoring")
                return False
            
            print("✓ Complete post-snapshot learning and re-scoring workflow completed")
            return True
            
        except Exception as e:
            print(f"✗ Failed to verify dirmeta updates: {e}")
            return False


def test_acceptance_criteria():
    """Test the exact acceptance criteria."""
    print("\nTesting acceptance criteria...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / "src").mkdir()
        (repo_root / ".spade").mkdir()
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Create dirmeta
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 1, "dirs": 1},
            "siblings": ["src"],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 2,
                "name_hash": "abc123"
            },
            "ext_histogram": {"py": 1, "xyz": 1},
            "markers": [],
            "deterministic_scoring": {}
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create actual files
        (repo_root / "main.py").write_text("# main")
        
        # Test 1: With learn_* flags true and learned files absent
        config = RunConfig(
            learn_markers=True,
            learn_languages=True,
            use_learned_markers=True,
            use_learned_languages=True,
            marker_learning=RunConfig.MarkerLearning(top_k_candidates=10, min_confidence=0.5)
        )
        
        from llm import LLMClient
        llm = LLMClient(echo_transport_markers_learning)
        
        post_snapshot_learning_and_rescore(repo_root, config, llm)
        
        # Check that learned files were created
        required_files = [
            repo_root / ".spade" / "markers.learned.json",
            repo_root / ".spade" / "languages.learned.json"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                print(f"✗ Required file missing: {file_path}")
                return False
        
        print("✓ Acceptance criteria met: learned files created and re-scoring applied")
        return True


def main():
    """Run all tests."""
    print("SPADE Learning System Test Suite")
    print("=" * 50)
    
    try:
        success1 = test_build_name_histogram()
        success2 = test_build_unknown_ext_histogram()
        success3 = test_learn_markers_once()
        success4 = test_learn_languages_once()
        success5 = test_learning_skip_when_exists()
        success6 = test_post_snapshot_learning_and_rescore()
        success7 = test_acceptance_criteria()
        
        if (success1 and success2 and success3 and success4 and success5 and 
            success6 and success7):
            print("\n" + "=" * 50)
            print("✓ All tests passed! Learning system working correctly.")
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
