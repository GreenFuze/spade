#!/usr/bin/env python3
"""
Test script for SPADE Phase-0 traversal system
Tests complete end-to-end workflow with DFS traversal, LLM calls, and persistence
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from phase0 import run_phase0
from worklist import WorklistStore
from models import RunConfig, Worklist
from dev.dummy_transport import echo_transport_valid_response


def test_worklist_store():
    """Test worklist store functionality."""
    print("Testing worklist store...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Test initialization
        worklist = WorklistStore(repo_root)
        
        # Test initial state
        wl = worklist.load()
        if wl.queue != ["."] or wl.visited != []:
            print(f"✗ Expected initial state queue=['.'], visited=[], got {wl.queue}, {wl.visited}")
            return False
        
        # Test push_many_left
        worklist.push_many_left(["src", "docs", "tests"])
        wl = worklist.load()
        if wl.queue != ["src", "docs", "tests", "."]:
            print(f"✗ Expected queue=['src', 'docs', 'tests', '.'], got {wl.queue}")
            return False
        
        # Test pop_left
        item = worklist.pop_left()
        if item != "src":
            print(f"✗ Expected popped item 'src', got {item}")
            return False
        
        wl = worklist.load()
        if wl.queue != ["docs", "tests", "."]:
            print(f"✗ Expected queue after pop ['docs', 'tests', '.'], got {wl.queue}")
            return False
        
        # Test mark_visited and is_visited
        worklist.mark_visited("/tmp/test")
        if not worklist.is_visited("/tmp/test"):
            print("✗ Expected /tmp/test to be marked as visited")
            return False
        
        if worklist.is_visited("/tmp/other"):
            print("✗ Expected /tmp/other to not be visited")
            return False
        
        print("✓ Worklist store works correctly")
        return True


def test_phase0_with_dummy_transport():
    """Test Phase-0 traversal with dummy transport."""
    print("\nTesting Phase-0 traversal with dummy transport...")
    
    # Create temporary directory with fakeapp structure
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal fakeapp structure
        (repo_root / "src").mkdir()
        (repo_root / "docs").mkdir()
        (repo_root / "tests").mkdir()
        (repo_root / ".spade").mkdir()
        
        # Create minimal run.json
        config = RunConfig(
            limits=RunConfig.Limits(max_depth=2, max_nodes=10, max_llm_calls=5),
            caps=RunConfig.Caps(nav=RunConfig.Caps.Nav(max_children_per_step=2))
        )
        (repo_root / ".spade" / "run.json").write_text(config.model_dump_json())
        
        # Create minimal snapshot structure
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Create root dirmeta
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 5, "dirs": 3},
            "siblings": ["src", "docs", "tests"],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 8,
                "name_hash": "abc123"
            },
            "deterministic_scoring": {
                "src": {"score": 0.9, "reasons": ["marker:package.json"]},
                "docs": {"score": 0.7, "reasons": ["lang:markdown"]},
                "tests": {"score": 0.5, "reasons": ["name:tests"]}
            }
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create child dirmeta
        for child in ["src", "docs", "tests"]:
            (repo_root / ".spade" / "snapshot" / child).mkdir()
            child_dirmeta = {
                "path": child,
                "depth": 1,
                "counts": {"files": 2, "dirs": 0},
                "siblings": [],
                "excluded_children": [],
                "staleness_fingerprint": {
                    "latest_modified_time": "2025-01-01T00:00:00Z",
                    "total_entries": 2,
                    "name_hash": f"def{child}"
                },
                "deterministic_scoring": {}
            }
            (repo_root / ".spade" / "snapshot" / child / "dirmeta.json").write_text(json.dumps(child_dirmeta))
        
        # Create minimal ignore specs
        (repo_root / ".spade" / ".spadeignore").write_text("")
        (repo_root / ".spade" / ".spadeallow").write_text("")
        
        # Run Phase-0
        try:
            run_phase0(repo_root, echo_transport_valid_response)
            print("✓ Phase-0 traversal completed successfully")
            
            # Check outputs
            analysis_root = repo_root / ".spade" / "analysis"
            if not analysis_root.exists():
                print("✗ Analysis directory not created")
                return False
            
            # Check that analysis files were created
            analysis_files = list(analysis_root.rglob("llm_inferred.json"))
            if len(analysis_files) == 0:
                print("✗ No analysis files created")
                return False
            
            print(f"✓ Created {len(analysis_files)} analysis files")
            
            # Check telemetry
            telemetry_path = repo_root / ".spade" / "telemetry.jsonl"
            if not telemetry_path.exists():
                print("✗ Telemetry file not created")
                return False
            
            telemetry_lines = telemetry_path.read_text().strip().split("\n")
            if len(telemetry_lines) == 0:
                print("✗ No telemetry lines written")
                return False
            
            print(f"✓ Wrote {len(telemetry_lines)} telemetry lines")
            
            # Check scaffold
            scaffold_path = repo_root / ".spade" / "scaffold"
            if not scaffold_path.exists():
                print("✗ Scaffold directory not created")
                return False
            
            # Check worklist
            worklist_path = repo_root / ".spade" / "worklist.json"
            if not worklist_path.exists():
                print("✗ Worklist file not created")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Phase-0 traversal failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_phase0_limits():
    """Test Phase-0 traversal with various limits."""
    print("\nTesting Phase-0 traversal with limits...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / "src").mkdir()
        (repo_root / ".spade").mkdir()
        
        # Test with very low limits
        config = RunConfig(
            limits=RunConfig.Limits(max_depth=1, max_nodes=1, max_llm_calls=1),
            caps=RunConfig.Caps(nav=RunConfig.Caps.Nav(max_children_per_step=1))
        )
        (repo_root / ".spade" / "run.json").write_text(config.model_dump_json())
        
        # Create minimal snapshot
        (repo_root / ".spade" / "snapshot").mkdir()
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
            "deterministic_scoring": {
                "src": {"score": 0.9, "reasons": ["marker:package.json"]}
            }
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Create ignore specs
        (repo_root / ".spade" / ".spadeignore").write_text("")
        (repo_root / ".spade" / ".spadeallow").write_text("")
        
        try:
            run_phase0(repo_root, echo_transport_valid_response)
            print("✓ Phase-0 traversal with limits completed")
            
            # Should have stopped due to limits
            telemetry_path = repo_root / ".spade" / "telemetry.jsonl"
            if telemetry_path.exists():
                telemetry_lines = telemetry_path.read_text().strip().split("\n")
                print(f"✓ Wrote {len(telemetry_lines)} telemetry lines with limits")
            
            return True
            
        except Exception as e:
            print(f"✗ Phase-0 traversal with limits failed: {e}")
            return False


def test_phase0_resume():
    """Test Phase-0 traversal resume capability."""
    print("\nTesting Phase-0 traversal resume capability...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create minimal structure
        (repo_root / "src").mkdir()
        (repo_root / "docs").mkdir()
        (repo_root / ".spade").mkdir()
        
        # Create config
        config = RunConfig(
            limits=RunConfig.Limits(max_depth=1, max_nodes=3, max_llm_calls=3),
            caps=RunConfig.Caps(nav=RunConfig.Caps.Nav(max_children_per_step=2))
        )
        (repo_root / ".spade" / "run.json").write_text(config.model_dump_json())
        
        # Create snapshot
        (repo_root / ".spade" / "snapshot").mkdir()
        
        # Root dirmeta
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
            "deterministic_scoring": {
                "src": {"score": 0.9, "reasons": ["marker:package.json"]},
                "docs": {"score": 0.7, "reasons": ["lang:markdown"]}
            }
        }
        (repo_root / ".spade" / "snapshot" / "dirmeta.json").write_text(json.dumps(root_dirmeta))
        
        # Child dirmeta
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
                "deterministic_scoring": {}
            }
            (repo_root / ".spade" / "snapshot" / child / "dirmeta.json").write_text(json.dumps(child_dirmeta))
        
        # Create ignore specs
        (repo_root / ".spade" / ".spadeignore").write_text("")
        (repo_root / ".spade" / ".spadeallow").write_text("")
        
        # Create existing worklist with partial progress
        existing_worklist = {
            "queue": ["docs"],
            "visited": [str((repo_root / "src").resolve())]
        }
        (repo_root / ".spade" / "worklist.json").write_text(json.dumps(existing_worklist))
        
        try:
            run_phase0(repo_root, echo_transport_valid_response)
            print("✓ Phase-0 traversal resume completed")
            
            # Check that worklist was updated
            worklist = WorklistStore(repo_root)
            wl = worklist.load()
            print(f"✓ Final worklist state: queue={len(wl.queue)}, visited={len(wl.visited)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Phase-0 traversal resume failed: {e}")
            return False


def test_acceptance_criteria():
    """Test the exact acceptance criteria."""
    print("\nTesting acceptance criteria...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        
        # Create test structure
        (repo_root / "src").mkdir()
        (repo_root / "docs").mkdir()
        (repo_root / ".spade").mkdir()
        
        # Create config
        config = RunConfig()
        (repo_root / ".spade" / "run.json").write_text(config.model_dump_json())
        
        # Create snapshot
        (repo_root / ".spade" / "snapshot").mkdir()
        root_dirmeta = {
            "path": ".",
            "depth": 0,
            "counts": {"files": 1, "dirs": 2},
            "siblings": ["src", "docs"],
            "excluded_children": [],
            "staleness_fingerprint": {
                "latest_modified_time": "2025-01-01T00:00:00Z",
                "total_entries": 3,
                "name_hash": "abc123"
            },
            "deterministic_scoring": {
                "src": {"score": 0.9, "reasons": ["marker:package.json"]},
                "docs": {"score": 0.7, "reasons": ["lang:markdown"]}
            }
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
                "deterministic_scoring": {}
            }
            (repo_root / ".spade" / "snapshot" / child / "dirmeta.json").write_text(json.dumps(child_dirmeta))
        
        # Create ignore specs
        (repo_root / ".spade" / ".spadeignore").write_text("")
        (repo_root / ".spade" / ".spadeallow").write_text("")
        
        try:
            run_phase0(repo_root, echo_transport_valid_response)
            
            # Check all required outputs exist
            required_paths = [
                repo_root / ".spade" / "analysis" / "llm_inferred.json",
                repo_root / ".spade" / "telemetry.jsonl",
                repo_root / ".spade" / "scaffold" / "repository_scaffold.json",
                repo_root / ".spade" / "scaffold" / "high_level_components.json",
                repo_root / ".spade" / "worklist.json"
            ]
            
            for path in required_paths:
                if not path.exists():
                    print(f"✗ Required output missing: {path}")
                    return False
            
            print("✓ All required outputs created")
            
            # Check telemetry format
            telemetry_lines = (repo_root / ".spade" / "telemetry.jsonl").read_text().strip().split("\n")
            if len(telemetry_lines) > 0:
                # Parse first line to check format
                first_line = json.loads(telemetry_lines[0])
                required_fields = ["step", "path", "depth", "prompt_chars", "response_chars", "duration_ms", "json_valid", "nav_requested", "nav_kept", "nav_rejected", "fallback_used"]
                for field in required_fields:
                    if field not in first_line:
                        print(f"✗ Telemetry missing required field: {field}")
                        return False
                
                print("✓ Telemetry format correct")
            
            return True
            
        except Exception as e:
            print(f"✗ Acceptance criteria test failed: {e}")
            return False


def main():
    """Run all tests."""
    print("SPADE Phase-0 Traversal Test Suite")
    print("=" * 50)
    
    try:
        success1 = test_worklist_store()
        success2 = test_phase0_with_dummy_transport()
        success3 = test_phase0_limits()
        success4 = test_phase0_resume()
        success5 = test_acceptance_criteria()
        
        if success1 and success2 and success3 and success4 and success5:
            print("\n" + "=" * 50)
            print("✓ All tests passed! Phase-0 traversal system working correctly.")
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
