#!/usr/bin/env python3
"""
Test V4 Phase 1 ONLY: Repository Overview for cmake_hello_world
"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from llm0.v4.phase1_repository_overview_agent_v4 import RepositoryOverviewAgentV4

async def test_phase1_only_cmake_hello_world():
    """Test Phase 1 ONLY: Repository Overview for cmake_hello_world."""
    print("INFO:test_phase1_only_cmake_hello_world:Running Phase 1 ONLY: Repository Overview...")
    
    # Use cmake_hello_world test repository
    test_repo_path = Path(__file__).parent.parent.parent / "test_repos" / "cmake_hello_world"
    
    if not test_repo_path.exists():
        print(f"ERROR: Test repository not found at {test_repo_path}")
        return False
    
    print(f"INFO:test_phase1_only_cmake_hello_world:Using repository: {test_repo_path}")
    
    try:
        # Create Phase 1 agent
        agent = RepositoryOverviewAgentV4(test_repo_path)
        
        # Run Phase 1
        start_time = time.time()
        result = await agent.execute_phase()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"INFO:test_phase1_only_cmake_hello_world:Phase 1 completed in {execution_time:.1f} seconds")
        
        # Extract key information for logging
        repo_name = result.get("repository_overview", {}).get("name", "Unknown")
        build_systems = result.get("repository_overview", {}).get("build_systems", [])
        source_dirs = result.get("repository_overview", {}).get("directory_structure", {}).get("source_dirs", [])
        
        print(f"INFO:test_phase1_only_cmake_hello_world:Repository: {repo_name}")
        print(f"INFO:test_phase1_only_cmake_hello_world:Build Systems: {build_systems}")
        print(f"INFO:test_phase1_only_cmake_hello_world:Source Dirs: {source_dirs}")
        
        print("[OK] Phase 1 ONLY test with cmake_hello_world passed")
        return True
        
    except Exception as e:
        print(f"ERROR:test_phase1_only_cmake_hello_world:Phase 1 failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase1_only_cmake_hello_world())
    if not success:
        sys.exit(1)
