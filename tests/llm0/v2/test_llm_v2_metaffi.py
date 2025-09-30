#!/usr/bin/env python3
"""
Test LLM RIG Generator V2 with MetaFFI repository.

This test validates the V2 approach with a large, multi-language repository.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator_v2 import LLMRIGGeneratorV2

def test_metaffi_repository():
    """Test the V2 approach with MetaFFI repository."""
    print("=" * 60)
    print("LLM RIG GENERATOR V2 METAEFFI TEST")
    print("=" * 60)
    
    # MetaFFI repository path
    metaffi_path = Path("C:/src/github.com/MetaFFI")
    
    if not metaffi_path.exists():
        print(f"ERROR: MetaFFI repository not found at {metaffi_path}")
        return False
    
    print(f"PATH: Using MetaFFI repository at: {metaffi_path}")
    
    try:
        # Initialize the generator
        print("INIT: Initializing LLM RIG Generator V2 for MetaFFI...")
        generator = LLMRIGGeneratorV2(metaffi_path)
        
        # Run complete RIG generation
        print("RUNNING: Complete RIG Generation (V2) for MetaFFI...")
        rig = generator.generate_rig()
        
        # Print results
        print(f"SUCCESS: Complete RIG generation completed!")
        print(f"COMPONENTS: Generated {len(rig.components)} components")
        print(f"TESTS: Generated {len(rig.tests)} tests")
        print(f"AGGREGATORS: Generated {len(rig.aggregators)} aggregators")
        print(f"RUNNERS: Generated {len(rig.runners)} runners")
        print(f"UTILITIES: Generated {len(rig.utilities)} utilities")
        print(f"MISSING FILES: {generator.missing_files} files requested but not found")
        print(f"FOUND FILES: {generator.found_files} files successfully read")
        
        # Print RIG info
        print(f"\nRIG INFO:")
        print(f"Repository: {rig.repository.name if rig.repository else 'Unknown'}")
        print(f"Build System: {rig.build_system.name if rig.build_system else 'Unknown'}")
        print(f"Components: {len(rig.components)}")
        print(f"Tests: {len(rig.tests)}")
        
        print("=" * 60)
        print("SUCCESS: LLM V2 MetaFFI test PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"ERROR: MetaFFI test failed: {e}")
        print("=" * 60)
        print("FAILED: LLM V2 MetaFFI test FAILED!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_metaffi_repository()
    sys.exit(0 if success else 1)
