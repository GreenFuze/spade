#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

import yaml

from spade.schemas import RunConfig


def test_yaml_structure():
    """Test that the YAML file structure is valid and matches the schema."""
    print("Testing YAML structure...")

    # Read the default YAML file
    yaml_path = Path("spade/default_run_phase0.yaml")
    if not yaml_path.exists():
        print(f"✗ YAML file not found: {yaml_path}")
        return False

    try:
        # Load YAML
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        print(f"✓ YAML loaded successfully")
        print(f"✓ Top-level keys: {list(yaml_data.keys())}")

        # Validate against schema
        config = RunConfig(**yaml_data)
        print(f"✓ Schema validation passed")
        print(f"✓ Model: {config.model}")
        print(f"✓ Caps samples max_dirs: {config.caps.samples.max_dirs}")
        print(f"✓ Limits max_depth: {config.limits.max_depth}")

        return True

    except Exception as e:
        print(f"✗ YAML validation failed: {e}")
        return False


if __name__ == "__main__":
    success = test_yaml_structure()
    if success:
        print("✓ All YAML validation tests passed!")
    else:
        print("✗ YAML validation tests failed!")
        sys.exit(1)
