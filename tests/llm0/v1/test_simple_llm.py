#!/usr/bin/env python3
"""
Simple LLM test to verify basic functionality works.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator import LLMRIGGenerator

def test_simple_llm():
    """Test basic LLM functionality with minimal requests."""
    print("=" * 60)
    print("SIMPLE LLM TEST")
    print("=" * 60)
    
    # Use the simple cmake_hello_world project
    test_project = Path(__file__).parent / "test_repos" / "cmake_hello_world"
    
    if not test_project.exists():
        print(f"ERROR: Test project not found at {test_project}")
        return False
    
    print(f"PATH: Using test project at: {test_project}")
    
    try:
        # Create generator with very low request limit to force efficiency
        generator = LLMRIGGenerator(test_project)
        generator.max_requests_per_phase = 10  # Very low limit to force efficiency
        
        print("INIT: Initializing LLM RIG Generator...")
        
        # Test just Phase 1 (Discovery) with minimal requests
        print("RUNNING: Testing Phase 1: Repository Discovery...")
        discovery_result = generator.discover_repository()
        
        if discovery_result.success:
            print("SUCCESS: Phase 1 completed successfully!")
            print(f"TOKENS: Phase 1 Token Usage: {discovery_result.token_usage['total_tokens']} tokens")
            print(f"REQUESTS: Used {generator.current_phase_requests} requests")
            return True
        else:
            print(f"ERROR: Phase 1 failed: {discovery_result.errors}")
            return False
            
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_simple_llm()
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Simple LLM test PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ERROR: Simple LLM test FAILED!")
        print("=" * 60)
        sys.exit(1)
