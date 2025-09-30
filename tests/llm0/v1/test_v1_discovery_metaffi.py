#!/usr/bin/env python3
"""
Test V1 Discovery phase specifically on MetaFFI repository.

This test isolates the Discovery phase to see if the original V1 approach
handles large repositories better than V2/V3.
"""

import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Add agentkit-gf to path
agentkit_gf_path = Path(__file__).parent / "agentkit_gf"
sys.path.insert(0, str(agentkit_gf_path))

from llm0_rig_generator import LLMRIGGenerator

async def test_v1_discovery_metaffi():
    """Test V1 Discovery phase on MetaFFI repository."""
    print("=" * 60)
    print("V1 DISCOVERY PHASE - MetaFFI TEST")
    print("=" * 60)
    
    # Test with MetaFFI repository
    test_path = Path("C:/src/github.com/MetaFFI")
    
    if not test_path.exists():
        print(f"ERROR: MetaFFI repository not found at {test_path}")
        return False
    
    print(f"PATH: Using MetaFFI repository at: {test_path}")
    
    try:
        # Initialize the V1 generator
        print("INIT: Initializing V1 LLM RIG Generator for MetaFFI...")
        generator = LLMRIGGenerator(test_path, openai_api_key="dummy_key")
        
        # Run only the Discovery phase
        print("RUNNING: V1 Discovery Phase on MetaFFI...")
        discovery_results = await generator.discover_repository()
        
        # Print results
        print(f"SUCCESS: V1 Discovery phase completed!")
        print(f"DISCOVERY RESULTS:")
        print(f"- Build System: {discovery_results.get('build_system', 'Unknown')}")
        print(f"- Components: {len(discovery_results.get('components', []))}")
        print(f"- Structure: {discovery_results.get('structure', 'Unknown')}")
        
        # Print detailed results
        print(f"\nDETAILED RESULTS:")
        import json
        print(json.dumps(discovery_results, indent=2))
        
        print("=" * 60)
        print("SUCCESS: V1 Discovery phase test PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"ERROR: V1 Discovery test failed: {e}")
        print("=" * 60)
        print("FAILED: V1 Discovery phase test FAILED!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_v1_discovery_metaffi())
    sys.exit(0 if success else 1)
