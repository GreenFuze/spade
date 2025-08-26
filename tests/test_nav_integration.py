#!/usr/bin/env python3
"""
Integration test for SPADE navigation guardrails
Tests navigation filtering with real dirmeta data
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from nav import filter_nav, fallback_children
from models import RunConfig, Nav, load_json, DirMeta
from ignore import load_specs


def test_nav_with_real_dirmeta():
    """Test navigation filtering with real dirmeta data."""
    print("Testing navigation filtering with real dirmeta...")
    
    # Create config
    cfg = RunConfig(
        limits=RunConfig.Limits(max_depth=3),
        caps=RunConfig.Caps(nav=RunConfig.Caps.Nav(max_children_per_step=2))
    )
    
    # Load real dirmeta from fakeapp
    repo_root = Path("fakeapp")
    dirmeta_path = repo_root / ".spade" / "snapshot" / "dirmeta.json"
    
    if not dirmeta_path.exists():
        print("✗ No dirmeta.json found in fakeapp/.spade/snapshot/")
        print("  Please run snapshot generation first")
        return False
    
    # Load and validate dirmeta
    current_meta = load_json(dirmeta_path, DirMeta)
    print(f"✓ Loaded dirmeta for path: {current_meta.path}")
    print(f"✓ Siblings: {current_meta.siblings}")
    print(f"✓ Excluded children: {current_meta.excluded_children}")
    
    # Load ignore specs
    specs = load_specs(repo_root)
    
    # Test 1: Valid navigation request
    nav_valid = Nav(descend_into=["src", "docs"], descend_one_level_only=True)
    kept, rejected = filter_nav(repo_root, current_meta, cfg, nav_valid, specs)
    
    print(f"✓ Valid nav kept: {kept}")
    print(f"✓ Valid nav rejected: {rejected}")
    
    # Test 2: Invalid navigation request
    nav_invalid = Nav(descend_into=["nonexistent", "src/subdir", ".", ".."], descend_one_level_only=True)
    kept_inv, rejected_inv = filter_nav(repo_root, current_meta, cfg, nav_invalid, specs)
    
    print(f"✓ Invalid nav kept: {kept_inv}")
    print(f"✓ Invalid nav rejected: {rejected_inv}")
    
    # Test 3: Fallback when nav is empty
    nav_empty = Nav(descend_into=[], descend_one_level_only=True)
    kept_empty, rejected_empty = filter_nav(repo_root, current_meta, cfg, nav_empty, specs)
    
    if not kept_empty:
        print("✓ Empty nav resulted in no kept children")
        
        # Test fallback
        fallback = fallback_children(repo_root, current_meta, cfg, specs)
        print(f"✓ Fallback children: {fallback}")
    else:
        print(f"✓ Empty nav kept: {kept_empty}")
    
    return True


def main():
    """Run integration test."""
    print("SPADE Navigation Integration Test")
    print("=" * 40)
    
    try:
        success = test_nav_with_real_dirmeta()
        
        if success:
            print("\n" + "=" * 40)
            print("✓ Integration test passed! Navigation guardrails work with real data.")
        else:
            print("\n" + "=" * 40)
            print("✗ Integration test failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
