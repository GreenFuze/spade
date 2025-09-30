#!/usr/bin/env python3
"""
Phase-by-phase LLM test for JNI project to avoid the "reading all files" problem.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm0_rig_generator import LLMRIGGenerator

def test_jni_phase_by_phase():
    """Test LLM functionality phase by phase with JNI project."""
    print("=" * 60)
    print("JNI PHASE-BY-PHASE LLM TEST")
    print("=" * 60)
    
    # Use the JNI project
    test_project = Path(__file__).parent / "test_repos" / "jni_hello_world"
    
    if not test_project.exists():
        print(f"ERROR: Test project not found at {test_project}")
        return False
    
    print(f"PATH: Using test project at: {test_project}")
    
    try:
        # Create generator with strict request limits
        generator = LLMRIGGenerator(test_project)
        generator.max_requests_per_phase = 20  # Slightly higher for more complex project
        
        print("INIT: Initializing LLM RIG Generator...")
        
        # Phase 1: Repository Discovery
        print("RUNNING: Phase 1: Repository Discovery...")
        generator._reset_request_counter()
        discovery_result = generator.discover_repository()
        
        if not discovery_result.success:
            print(f"ERROR: Phase 1 failed: {discovery_result.errors}")
            return False
        
        print("SUCCESS: Phase 1 completed!")
        print(f"TOKENS: Phase 1 Token Usage: {discovery_result.token_usage['total_tokens']} tokens")
        print(f"REQUESTS: Used {generator.current_phase_requests} requests")
        
        # Phase 2: Component Classification
        print("\nRUNNING: Phase 2: Component Classification...")
        generator._reset_request_counter()
        classification_result = generator.classify_components(discovery_result)
        
        if not classification_result["success"]:
            print(f"ERROR: Phase 2 failed: {classification_result['errors']}")
            return False
        
        print("SUCCESS: Phase 2 completed!")
        print(f"TOKENS: Phase 2 Token Usage: {classification_result['token_usage']['total_tokens']} tokens")
        print(f"REQUESTS: Used {generator.current_phase_requests} requests")
        
        # Phase 3: Relationship Mapping
        print("\nRUNNING: Phase 3: Relationship Mapping...")
        generator._reset_request_counter()
        relationship_result = generator.map_relationships(discovery_result, classification_result)
        
        if not relationship_result["success"]:
            print(f"ERROR: Phase 3 failed: {relationship_result['errors']}")
            return False
        
        print("SUCCESS: Phase 3 completed!")
        print(f"TOKENS: Phase 3 Token Usage: {relationship_result['token_usage']['total_tokens']} tokens")
        print(f"REQUESTS: Used {generator.current_phase_requests} requests")
        
        # Phase 4: RIG Assembly
        print("\nRUNNING: Phase 4: RIG Assembly...")
        generator._reset_request_counter()
        assembly_result = generator.assemble_rig(discovery_result, classification_result, relationship_result)
        
        if not assembly_result["success"]:
            print(f"ERROR: Phase 4 failed: {assembly_result['errors']}")
            return False
        
        print("SUCCESS: Phase 4 completed!")
        print(f"TOKENS: Phase 4 Token Usage: {assembly_result['token_usage']['total_tokens']} tokens")
        print(f"REQUESTS: Used {generator.current_phase_requests} requests")
        
        # Calculate totals
        total_tokens = (
            discovery_result.token_usage['total_tokens'] +
            classification_result['token_usage']['total_tokens'] +
            relationship_result['token_usage']['total_tokens'] +
            assembly_result['token_usage']['total_tokens']
        )
        
        print(f"\nTOTAL: Total Token Usage: {total_tokens} tokens")
        print(f"TOTAL: Total Requests: {generator.current_phase_requests} requests")
        
        return True
            
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_jni_phase_by_phase()
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: JNI Phase-by-phase LLM test PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ERROR: JNI Phase-by-phase LLM test FAILED!")
        print("=" * 60)
        sys.exit(1)
