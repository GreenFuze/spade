"""
Test V6 Phases 1-4: Complete Pipeline Test

This test validates the V6 phases 1-4 with the cmake_hello_world repository.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import pytest
import asyncio
from pathlib import Path

from llm0.v6 import (
    RepositoryOverviewAgentV6,
    SourceStructureDiscoveryAgentV6,
    TestStructureDiscoveryAgentV6,
    BuildSystemAnalysisAgentV6
)


@pytest.mark.asyncio
async def test_v6_phases1_4_cmake_hello_world():
    """Test V6 Phases 1-4 with cmake_hello_world repository."""
    repo_path = Path("tests/test_repos/cmake_hello_world")
    model_settings = {"temperature": 0, "model": "gpt-5-nano"}

    # Phase 1: Repository Overview
    print("🔍 Phase 1: Repository Overview")
    phase1_agent = RepositoryOverviewAgentV6(repo_path, model_settings)
    phase1_store = await phase1_agent.execute_phase()
    
    assert phase1_store.is_valid(), f"Phase 1 store validation failed: {phase1_store.get_validation_errors()}"
    print(f"✅ Phase 1 completed: {phase1_store.get_summary()}")
    
    # Phase 2: Source Structure Discovery
    print("\n🔍 Phase 2: Source Structure Discovery")
    phase2_agent = SourceStructureDiscoveryAgentV6(repo_path, model_settings)
    phase2_store = await phase2_agent.execute_phase([phase1_store])
    
    assert phase2_store.is_valid(), f"Phase 2 store validation failed: {phase2_store.get_validation_errors()}"
    print(f"✅ Phase 2 completed: {phase2_store.get_summary()}")
    
    # Phase 3: Test Structure Discovery
    print("\n🔍 Phase 3: Test Structure Discovery")
    phase3_agent = TestStructureDiscoveryAgentV6(repo_path, model_settings)
    phase3_store = await phase3_agent.execute_phase([phase1_store, phase2_store])
    
    assert phase3_store.is_valid(), f"Phase 3 store validation failed: {phase3_store.get_validation_errors()}"
    print(f"✅ Phase 3 completed: {phase3_store.get_summary()}")
    
    # Phase 4: Build System Analysis
    print("\n🔍 Phase 4: Build System Analysis")
    phase4_agent = BuildSystemAnalysisAgentV6(repo_path, model_settings)
    phase4_store = await phase4_agent.execute_phase([phase1_store, phase2_store, phase3_store])
    
    assert phase4_store.is_valid(), f"Phase 4 store validation failed: {phase4_store.get_validation_errors()}"
    print(f"✅ Phase 4 completed: {phase4_store.get_summary()}")
    
    # Validate overall pipeline results
    print("\n📊 Pipeline Summary:")
    print(f"Phase 1 - Repository: {phase1_store.name} ({phase1_store.type})")
    print(f"Phase 2 - Components: {len(phase2_store._components)}")
    print(f"Phase 3 - Test Components: {len(phase3_store.test_components)}")
    print(f"Phase 4 - Build Targets: {len(phase4_store.build_targets)}")
    
    # Check specific expectations for cmake_hello_world
    assert "cmake" in [bs.lower() for bs in phase1_store.build_systems], "CMake should be identified as build system"
    assert len(phase2_store._components) >= 2, "Should have at least 2 source components (main + utils)"
    assert len(phase4_store.build_targets) >= 2, "Should have at least 2 build targets (hello_world + utils)"
    
    print("\n✅ V6 Phases 1-4 test passed!")


if __name__ == "__main__":
    asyncio.run(test_v6_phases1_4_cmake_hello_world())
