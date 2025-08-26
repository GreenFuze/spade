#!/usr/bin/env python3
"""
Test script for configuration loading with Pydantic models
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from workspace import Workspace


def test_config_loading():
    """Test loading configuration from workspace."""
    print("Testing configuration loading...")
    
    # Load configuration from fakeapp workspace
    config = Workspace.load_config(Path("fakeapp"))
    
    print(f"✓ Configuration loaded successfully:")
    print(f"  - max_depth: {config.limits.max_depth}")
    print(f"  - max_nodes: {config.limits.max_nodes}")
    print(f"  - max_llm_calls: {config.limits.max_llm_calls}")
    print(f"  - max_children_per_step: {config.caps.nav.max_children_per_step}")
    print(f"  - name_signals: {config.scoring.name_signals}")
    print(f"  - skip_symlinks: {config.policies.skip_symlinks}")
    print(f"  - descend_one_level_only: {config.policies.descend_one_level_only}")
    
    # Test that we can access nested fields
    assert config.limits.max_depth == 6
    assert config.limits.max_nodes == 2000
    assert config.caps.nav.max_children_per_step == 4
    assert "api" in config.scoring.name_signals
    assert config.policies.skip_symlinks is True
    
    print("✓ All configuration values match expected defaults")
    print("✓ Pydantic model validation working correctly")


if __name__ == "__main__":
    test_config_loading()
