#!/usr/bin/env python3
"""
Test V4 Phase 2 ONLY: Source Structure Discovery for jni_hello_world
"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase2_source_structure_agent_v4 import SourceStructureDiscoveryAgentV4

async def test_phase2_only_jni_hello_world():
    """Test Phase 2 ONLY: Source Structure Discovery for jni_hello_world."""
    print("INFO:test_phase2_only_jni_hello_world:Running Phase 2 ONLY: Source Structure Discovery...")
    
    # Use jni_hello_world test repository
    test_repo_path = Path(__file__).parent.parent.parent / "test_repos" / "jni_hello_world"
    
    if not test_repo_path.exists():
        print(f"ERROR: Test repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase2_only_jni_hello_world:Using repository: {test_repo_path}")
    
    # Create mock Phase 1 results for jni_hello_world
    phase1_results = {
        "repository_overview": {
            "name": "jni_hello_world",
            "type": "application",
            "primary_language": "multi-language (C++/Java)",
            "build_systems": ["cmake"],
            "directory_structure": {
                "source_dirs": ["src"],
                "test_dirs": ["tests"],
                "build_dirs": ["build"],
                "config_dirs": []
            },
            "entry_points": ["CMakeLists.txt"],
            "exploration_scope": {
                "priority_dirs": ["src", "tests"],
                "skip_dirs": [".git", "build", "node_modules"],
                "deep_exploration": ["src", "tests"]
            }
        }
    }
    
    try:
        # Create Phase 2 agent
        agent = SourceStructureDiscoveryAgentV4(test_repo_path)
        
        # Run Phase 2 with Phase 1 results
        start_time = time.time()
        result = await agent.execute_phase(phase1_results)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"INFO:test_phase2_only_jni_hello_world:Phase 2 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        components = result.get("source_structure", {}).get("components", [])
        files = result.get("source_structure", {}).get("files", [])
        
        print(f"INFO:test_phase2_only_jni_hello_world:Components found: {len(components)}")
        print(f"INFO:test_phase2_only_jni_hello_world:Files analyzed: {len(files)}")
        
        print("[OK] Phase 2 ONLY test with jni_hello_world passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase2_only_jni_hello_world:Phase 2 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase2_only_jni_hello_world())
    if not success:
        sys.exit(1)
