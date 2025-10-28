"""
Test V6 Phase 2: Source Structure Discovery Agent

This test validates the V6 Phase 2 agent with the cmake_hello_world repository.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import pytest
import asyncio
from pathlib import Path

from llm0.v6 import SourceStructureDiscoveryAgentV6, RepositoryOverviewAgentV6


@pytest.mark.asyncio
async def test_v6_phase2_cmake_hello_world():
    """Test V6 Phase 2 with cmake_hello_world repository."""
    repo_path = Path("tests/test_repos/cmake_hello_world")
    model_settings = {"temperature": 0, "model": "gpt-5-nano"}

    # First execute Phase 1 to get the phase store
    phase1_agent = RepositoryOverviewAgentV6(repo_path, model_settings)
    phase1_store = await phase1_agent.execute_phase()
    
    # Validate Phase 1 results
    assert phase1_store.is_valid(), f"Phase 1 store validation failed: {phase1_store.get_validation_errors()}"
    
    # Now execute Phase 2 with Phase 1 results
    phase2_agent = SourceStructureDiscoveryAgentV6(repo_path, model_settings)
    phase2_store = await phase2_agent.execute_phase([phase1_store])
    
    # Validate Phase 2 results
    assert phase2_store is not None
    assert phase2_store.is_valid(), f"Phase 2 store validation failed: {phase2_store.get_validation_errors()}"
    
    # Check basic requirements
    assert len(phase2_store._components) > 0, "At least one source component should be identified"
    assert phase2_store.language_analysis.primary_language is not None, "Primary language should be set"
    assert len(phase2_store.file_organization) > 0, "File organization information should be available"
    
    # Check specific expectations for cmake_hello_world
    component_names = [c.name for c in phase2_store._components]
    assert "main" in component_names or "hello_world" in component_names, "Main component should be identified"
    
    # Check that components have files
    for component in phase2_store._components:
        assert len(component.files) > 0, f"Component '{component.name}' should have files"
        assert component.language is not None, f"Component '{component.name}' should have a language"
    
    # Print summary for debugging
    summary = phase2_store.get_summary()
    print(f"Phase 2 Summary: {summary}")
    
    print("✅ V6 Phase 2 test passed!")


if __name__ == "__main__":
    asyncio.run(test_v6_phase2_cmake_hello_world())
