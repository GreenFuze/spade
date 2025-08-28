#!/usr/bin/env python3
"""
Integration test for LLM client with real context
Tests the full pipeline from context building to LLM response
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from context import build_phase0_context
from llm import LLMClient
from dev.dummy_transport import echo_transport_valid_response
from schemas import RunConfig


def test_llm_with_real_context():
    """Test LLM client with real context from context builder."""
    print("Testing LLM client with real context...")
    
    # Create a minimal config
    config = RunConfig()
    
    # Build real context using context builder
    repo_root = Path("fakeapp")
    context = build_phase0_context(repo_root, ".", config)
    
    print(f"✓ Context built successfully with {len(context.get('siblings', []))} siblings")
    
    # Test LLM client with real context
    client = LLMClient(echo_transport_valid_response)
    response, raw = client.call_phase0(context)
    
    if response is not None:
        print("✓ LLM client processed real context successfully")
        print(f"✓ Response has {len(response.inferred.high_level_components)} components")
        print(f"✓ Response has {len(response.inferred.nodes)} nodes")
        print(f"✓ Navigation suggests {len(response.nav.descend_into)} directories")
        return True
    else:
        print("✗ LLM client failed to process real context")
        return False


def main():
    """Run integration test."""
    print("SPADE LLM Integration Test")
    print("=" * 40)
    
    try:
        success = test_llm_with_real_context()
        
        if success:
            print("\n" + "=" * 40)
            print("✓ Integration test passed! LLM client works with real context.")
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
