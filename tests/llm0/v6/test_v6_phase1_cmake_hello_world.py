"""
Test V6 Phase 1: Repository Overview Agent

This test validates the V6 Phase 1 agent with the cmake_hello_world repository.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import pytest
import asyncio
from pathlib import Path

from llm0.v6 import RepositoryOverviewAgentV6


@pytest.mark.asyncio
async def test_v6_phase1_cmake_hello_world():
    """Test V6 Phase 1 with cmake_hello_world repository."""
    repo_path = Path("tests/test_repos/cmake_hello_world")
    model_settings = {"temperature": 0, "model": "gpt-5-nano"}

    # Create Phase 1 agent
    agent = RepositoryOverviewAgentV6(repo_path, model_settings)
    
    # Execute Phase 1
    phase1_store = await agent.execute_phase()
    
    # Validate results
    assert phase1_store is not None
    assert phase1_store.is_valid(), f"Phase 1 store validation failed: {phase1_store.get_validation_errors()}"
    
    # Check basic requirements
    assert phase1_store.name is not None, "Repository name should be set"
    assert phase1_store.type is not None, "Repository type should be set"
    assert phase1_store.primary_language is not None, "Primary language should be set"
    assert len(phase1_store.build_systems) > 0, "At least one build system should be identified"
    assert len(phase1_store.directory_structure.source_dirs) > 0, "At least one source directory should be identified"
    assert len(phase1_store.entry_points) > 0, "At least one entry point should be identified"
    assert len(phase1_store.exploration_scope.priority_dirs) > 0, "At least one priority directory should be identified"
    
    # Check specific expectations for cmake_hello_world
    assert "cmake" in [bs.lower() for bs in phase1_store.build_systems], "CMake should be identified as build system"
    assert "cpp" in phase1_store.primary_language.lower() or "c++" in phase1_store.primary_language.lower(), "C++ should be identified as primary language"
    
    # Print summary for debugging
    summary = phase1_store.get_summary()
    print(f"Phase 1 Summary: {summary}")
    
    print("✅ V6 Phase 1 test passed!")


if __name__ == "__main__":
    asyncio.run(test_v6_phase1_cmake_hello_world())
