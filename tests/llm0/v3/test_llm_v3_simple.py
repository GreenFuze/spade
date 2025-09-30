#!/usr/bin/env python3
"""
Test LLM RIG Generator V3 Simple with separate agents for each phase.
"""

import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator_v3_simple import LLMRIGGeneratorV3Simple

async def test_v3_simple():
    """Test the V3 simple approach with separate agents."""
    print("=" * 60)
    print("LLM RIG GENERATOR V3 SIMPLE TEST")
    print("=" * 60)
    
    # Test with cmake_hello_world
    test_path = Path("test_repos/cmake_hello_world")
    
    if not test_path.exists():
        print(f"ERROR: Test repository not found at {test_path}")
        return False
    
    print(f"PATH: Using test project at: {test_path}")
    
    try:
        # Initialize the generator
        print("INIT: Initializing LLM RIG Generator V3 Simple...")
        generator = LLMRIGGeneratorV3Simple(test_path)
        
        # Run complete RIG generation
        print("RUNNING: Complete RIG Generation (V3 Simple)...")
        rig = await generator.generate_rig()
        
        # Print results
        print(f"SUCCESS: Complete RIG generation completed!")
        print(f"COMPONENTS: Generated {len(rig.components)} components")
        print(f"TESTS: Generated {len(rig.tests)} tests")
        print(f"AGGREGATORS: Generated {len(rig.aggregators)} aggregators")
        print(f"RUNNERS: Generated {len(rig.runners)} runners")
        print(f"UTILITIES: Generated {len(rig.utilities)} utilities")
        
        # Print RIG info
        print(f"\nRIG INFO:")
        print(f"Repository: {rig.repository.name if rig.repository else 'Unknown'}")
        print(f"Build System: {rig.build_system.name if rig.build_system else 'Unknown'}")
        print(f"Components: {len(rig.components)}")
        print(f"Tests: {len(rig.tests)}")
        
        print("=" * 60)
        print("SUCCESS: LLM V3 Simple test PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"ERROR: V3 Simple test failed: {e}")
        print("=" * 60)
        print("FAILED: LLM V3 Simple test FAILED!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_v3_simple())
    sys.exit(0 if success else 1)
