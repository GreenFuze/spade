#!/usr/bin/env python3
"""
Test V1 approach (single agent, no directory listing) on MetaFFI.
This will help identify which phase fails and why.
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

async def test_v1_simple_metaffi():
    """Test V1 approach on MetaFFI to see which phase fails."""
    print("=" * 60)
    print("V1 SIMPLE TEST - MetaFFI")
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
        
        # Test just the Discovery phase first
        print("RUNNING: V1 Discovery Phase on MetaFFI...")
        print("NOTE: This will test if Discovery phase completes before hitting iteration limit")
        
        discovery_results = await generator.discover_repository()
        
        print(f"SUCCESS: V1 Discovery phase completed!")
        print(f"DISCOVERY RESULTS:")
        print(f"- Build System: {discovery_results.get('build_system', 'Unknown')}")
        print(f"- Components: {len(discovery_results.get('components', []))}")
        
        print("=" * 60)
        print("SUCCESS: V1 Discovery phase PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"ERROR: V1 Discovery test failed: {e}")
        print("=" * 60)
        print("FAILED: V1 Discovery phase FAILED!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_v1_simple_metaffi())
    sys.exit(0 if success else 1)
