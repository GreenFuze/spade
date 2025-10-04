#!/usr/bin/env python3
"""
Test the LLM RIG Generator V2 with JNI project to verify scalability.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator_v2 import LLMRIGGeneratorV2

def test_llm_v2_jni():
    """Test the V2 approach with JNI project to verify scalability."""
    print("=" * 60)
    print("LLM RIG GENERATOR V2 JNI TEST")
    print("=" * 60)
    
    # Use the JNI project
    test_project = Path(__file__).parent / "test_repos" / "jni_hello_world"
    
    if not test_project.exists():
        print(f"ERROR: JNI test project not found at {test_project}")
        return False
    
    print(f"PATH: Using JNI test project at: {test_project}")
    
    try:
        # Create generator V2
        generator = LLMRIGGeneratorV2(test_project)
        generator.max_requests_per_phase = 30  # Higher limit for more complex project
        
        print("INIT: Initializing LLM RIG Generator V2 for JNI project...")
        
        # Test complete RIG generation with V2 approach
        print("RUNNING: Complete RIG Generation (V2) for JNI project...")
        rig = generator.generate_rig()
        
        print("SUCCESS: Complete RIG generation completed!")
        print(f"COMPONENTS: Generated {len(rig.components)} components")
        print(f"TESTS: Generated {len(rig.tests)} tests")
        print(f"AGGREGATORS: Generated {len(rig.aggregators)} aggregators")
        print(f"RUNNERS: Generated {len(rig.runners)} runners")
        print(f"UTILITIES: Generated {len(rig.utilities)} utilities")
        print(f"MISSING FILES: {len(generator.missing_files)} files requested but not found")
        print(f"FOUND FILES: {len(generator.found_files)} files successfully read")
        
        # Show basic RIG info
        print(f"\nRIG INFO:")
        print(f"Repository: {rig.repository.name if rig.repository else 'Unknown'}")
        print(f"Build System: {rig.build_system.name if rig.build_system else 'Unknown'}")
        print(f"Components: {len(rig.components)}")
        print(f"Tests: {len(rig.tests)}")
        
        return True
            
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_llm_v2_jni()
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: LLM V2 JNI test PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ERROR: LLM V2 JNI test FAILED!")
        print("=" * 60)
        sys.exit(1)
