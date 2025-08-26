#!/usr/bin/env python3
"""
Test script for SPADE snapshot functionality
Validates that snapshot scanning works correctly
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from snapshot import build_snapshot, get_file_extension, iso8601_z_of, sha1_of
from workspace import Workspace
from models import load_json, DirMeta


def test_extension_rules():
    """Test file extension extraction rules."""
    print("Testing file extension rules...")
    
    test_cases = [
        (".env", ".env"),           # Hidden dotfile
        ("file.txt", "txt"),        # Simple extension
        ("file.backup.txt", "txt"), # Multi-dot file
        ("noextension", ""),        # No extension
        (".gitignore", ".gitignore"), # Hidden file with extension (kept as whole name)
        ("config.backup.tar.gz", "gz"), # Complex multi-dot
    ]
    
    for filename, expected in test_cases:
        result = get_file_extension(filename)
        if result == expected:
            print(f"✓ {filename:20} → {result}")
        else:
            print(f"✗ {filename:20} → {result} (expected {expected})")
            return False
    
    return True


def test_helpers():
    """Test helper functions."""
    print("\nTesting helper functions...")
    
    # Test ISO-8601 conversion
    test_time = 1703001600.0  # 2023-12-19 16:00:00 UTC
    iso_time = iso8601_z_of(test_time)
    expected = "2023-12-19T16:00:00Z"
    if iso_time == expected:
        print(f"✓ ISO-8601 conversion: {iso_time}")
    else:
        print(f"✗ ISO-8601 conversion: {iso_time} (expected {expected})")
        return False
    
    # Test SHA-1 hash
    test_names = ["file1.txt", "file2.py", "dir1"]
    hash_result = sha1_of(test_names)
    if len(hash_result) == 40:  # SHA-1 hex digest length
        print(f"✓ SHA-1 hash: {hash_result[:8]}...")
    else:
        print(f"✗ SHA-1 hash length: {len(hash_result)}")
        return False
    
    return True


def test_snapshot_build():
    """Test snapshot building with fakeapp repository."""
    print("\nTesting snapshot build...")
    
    repo_root = Path("fakeapp")
    
    # Load configuration
    try:
        config = Workspace.load_config(repo_root)
        print("✓ Loaded configuration")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False
    
    # Build snapshot
    try:
        build_snapshot(repo_root, config)
        print("✓ Snapshot build completed")
    except Exception as e:
        print(f"✗ Snapshot build failed: {e}")
        return False
    
    # Verify snapshot files were created
    snapshot_dir = repo_root / ".spade" / "snapshot"
    if not snapshot_dir.exists():
        print(f"✗ Snapshot directory not created: {snapshot_dir}")
        return False
    
    # Check for root dirmeta
    root_dirmeta_path = snapshot_dir / "dirmeta.json"
    if not root_dirmeta_path.exists():
        print(f"✗ Root dirmeta not created: {root_dirmeta_path}")
        return False
    
    # Load and validate root dirmeta
    try:
        root_dirmeta = load_json(root_dirmeta_path, DirMeta)
        print(f"✓ Root dirmeta loaded: {root_dirmeta.path}")
        print(f"  - files: {root_dirmeta.counts.files}")
        print(f"  - dirs: {root_dirmeta.counts.dirs}")
        print(f"  - depth: {root_dirmeta.depth}")
        print(f"  - ext_histogram: {root_dirmeta.ext_histogram}")
    except Exception as e:
        print(f"✗ Failed to load root dirmeta: {e}")
        return False
    
    # Check for subdirectory dirmeta files
    subdirs = ["src", "tests", "docs"]
    for subdir in subdirs:
        subdir_dirmeta_path = snapshot_dir / subdir / "dirmeta.json"
        if subdir_dirmeta_path.exists():
            try:
                subdir_dirmeta = load_json(subdir_dirmeta_path, DirMeta)
                print(f"✓ {subdir} dirmeta: {subdir_dirmeta.counts.files} files, {subdir_dirmeta.counts.dirs} dirs")
            except Exception as e:
                print(f"✗ Failed to load {subdir} dirmeta: {e}")
                return False
        else:
            print(f"⚠ {subdir} dirmeta not found (may be expected)")
    
    # Check that ignored directories are not processed
    node_modules_dirmeta_path = snapshot_dir / "node_modules" / "dirmeta.json"
    if node_modules_dirmeta_path.exists():
        try:
            node_modules_dirmeta = load_json(node_modules_dirmeta_path, DirMeta)
            if node_modules_dirmeta.ignored_reason:
                print(f"✓ node_modules properly ignored: {node_modules_dirmeta.ignored_reason}")
            else:
                print(f"✗ node_modules not properly ignored")
                return False
        except Exception as e:
            print(f"✗ Failed to load node_modules dirmeta: {e}")
            return False
    else:
        print("⚠ node_modules dirmeta not found (may be expected)")
    
    return True


def validate_dirmeta_structure(dirmeta: DirMeta):
    """Validate dirmeta structure and content."""
    print(f"\nValidating dirmeta structure for {dirmeta.path}...")
    
    # Check required fields
    required_fields = ['path', 'depth', 'counts', 'ext_histogram', 'markers', 
                      'samples', 'siblings', 'excluded_children', 'is_symlink', 
                      'ignored_reason', 'staleness_fingerprint', 'deterministic_scoring']
    
    for field in required_fields:
        if not hasattr(dirmeta, field):
            print(f"✗ Missing field: {field}")
            return False
    
    # Check counts
    if dirmeta.counts.files < 0 or dirmeta.counts.dirs < 0:
        print(f"✗ Invalid counts: files={dirmeta.counts.files}, dirs={dirmeta.counts.dirs}")
        return False
    
    # Check depth
    if dirmeta.depth < 0:
        print(f"✗ Invalid depth: {dirmeta.depth}")
        return False
    
    # Check staleness fingerprint
    fp = dirmeta.staleness_fingerprint
    if fp.total_entries < 0:
        print(f"✗ Invalid total_entries: {fp.total_entries}")
        return False
    
    if not fp.latest_modified_time.endswith('Z'):
        print(f"✗ Invalid timestamp format: {fp.latest_modified_time}")
        return False
    
    if len(fp.name_hash) != 40:
        print(f"✗ Invalid name_hash length: {len(fp.name_hash)}")
        return False
    
    # Check samples
    if len(dirmeta.samples.dirs) > 8:  # max_dirs default
        print(f"✗ Too many sample dirs: {len(dirmeta.samples.dirs)}")
        return False
    
    if len(dirmeta.samples.files) > 8:  # max_files default
        print(f"✗ Too many sample files: {len(dirmeta.samples.files)}")
        return False
    
    print("✓ Dirmeta structure is valid")
    return True


def main():
    """Run all tests."""
    print("SPADE Snapshot Test Suite")
    print("=" * 50)
    
    try:
        success1 = test_extension_rules()
        success2 = test_helpers()
        success3 = test_snapshot_build()
        
        if success1 and success2 and success3:
            print("\n" + "=" * 50)
            print("✓ All tests passed! Snapshot functionality working correctly.")
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
