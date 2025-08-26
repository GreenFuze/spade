#!/usr/bin/env python3
"""
Test script for SPADE JSON helper functions
Validates load_json and save_json functionality
"""

import tempfile
from pathlib import Path
from models import RunConfig, load_json, save_json


def test_json_helpers():
    """Test JSON helper functions."""
    print("Testing JSON helpers...")
    
    # Create a test config
    config = RunConfig()
    config.limits.max_depth = 10
    config.limits.max_nodes = 5000
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Test save_json
        save_json(temp_path, config)
        print(f"✓ Config saved to {temp_path}")
        
        # Test load_json
        loaded_config = load_json(temp_path, RunConfig)
        print(f"✓ Config loaded from {temp_path}")
        
        # Verify data integrity
        assert loaded_config.limits.max_depth == 10
        assert loaded_config.limits.max_nodes == 5000
        print("✓ Data integrity verified")
        
        # Test with default values
        default_config = RunConfig()
        assert default_config.limits.max_depth == 6
        assert default_config.limits.max_nodes == 2000
        print("✓ Default values verified")
        
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()
    
    print("✓ JSON helpers working correctly")


if __name__ == "__main__":
    test_json_helpers()
