#!/usr/bin/env python3
"""
V5 LLM-based RIG Generator with Direct RIG Manipulation

This module implements the V5 architecture where all agents work with a single
RIG instance that grows incrementally through all phases, eliminating JSON
conversion issues and providing type safety.
"""

import logging
from pathlib import Path
from typing import Optional

from core.rig import RIG
from .base_agent_v5 import BaseLLMAgentV5
from .phase1_repository_overview_agent_v5 import RepositoryOverviewAgentV5
from .phase2_source_structure_agent_v5 import SourceStructureDiscoveryAgentV5
from .phase3_test_structure_agent_v5 import TestStructureDiscoveryAgentV5
from .phase4_build_system_analysis_agent_v5 import BuildSystemAnalysisAgentV5
from .phase5_artifact_discovery_agent_v5 import ArtifactDiscoveryAgentV5
from .phase6_component_classification_agent_v5 import ComponentClassificationAgentV5
from .phase7_relationship_mapping_agent_v5 import RelationshipMappingAgentV5
from .phase8_rig_assembly_agent_v5 import RIGAssemblyAgentV5


class LLMRIGGeneratorV5:
    """V5 RIG Generator with direct RIG manipulation."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("LLMRIGGeneratorV5")
        self.logger.setLevel(logging.INFO)
        
        # Create a single RIG instance that will grow through all phases
        self.rig = RIG()
        
        # Initialize all phase agents with the same RIG instance
        self.phase1_agent = RepositoryOverviewAgentV5(self.repository_path, self.rig)
        self.phase2_agent = SourceStructureDiscoveryAgentV5(self.repository_path, self.rig)
        self.phase3_agent = TestStructureDiscoveryAgentV5(self.repository_path, self.rig)
        self.phase4_agent = BuildSystemAnalysisAgentV5(self.repository_path, self.rig)
        self.phase5_agent = ArtifactDiscoveryAgentV5(self.repository_path, self.rig)
        self.phase6_agent = ComponentClassificationAgentV5(self.repository_path, self.rig)
        self.phase7_agent = RelationshipMappingAgentV5(self.repository_path, self.rig)
        self.phase8_agent = RIGAssemblyAgentV5(self.repository_path, self.rig)
        
        self.logger.info(f"Initialized V5 RIG Generator for: {self.repository_path}")
        self.logger.info(f"Initial RIG state: {self.rig}")
    
    async def generate_rig(self) -> RIG:
        """Generate RIG using V5 architecture with single RIG instance flow."""
        self.logger.info("RUNNING: V5 RIG Generation (Direct RIG Manipulation)...")
        
        try:
            # Phase 1: Repository Overview
            self.logger.info("=== PHASE 1: Repository Overview ===")
            phase1_result = await self.phase1_agent.execute_phase()
            self.logger.info(f"Phase 1 result: {phase1_result}")
            
            # Phase 2: Source Structure Discovery
            self.logger.info("=== PHASE 2: Source Structure Discovery ===")
            phase2_result = await self.phase2_agent.execute_phase()
            self.logger.info(f"Phase 2 result: {phase2_result}")
            
            # Phase 3: Test Structure Discovery
            self.logger.info("=== PHASE 3: Test Structure Discovery ===")
            phase3_result = await self.phase3_agent.execute_phase()
            self.logger.info(f"Phase 3 result: {phase3_result}")
            
            # Phase 4: Build System Analysis
            self.logger.info("=== PHASE 4: Build System Analysis ===")
            phase4_result = await self.phase4_agent.execute_phase()
            self.logger.info(f"Phase 4 result: {phase4_result}")
            
            # Phase 5: Artifact Discovery
            self.logger.info("=== PHASE 5: Artifact Discovery ===")
            phase5_result = await self.phase5_agent.execute_phase()
            self.logger.info(f"Phase 5 result: {phase5_result}")
            
            # Phase 6: Component Classification
            self.logger.info("=== PHASE 6: Component Classification ===")
            phase6_result = await self.phase6_agent.execute_phase()
            self.logger.info(f"Phase 6 result: {phase6_result}")
            
            # Phase 7: Relationship Mapping
            self.logger.info("=== PHASE 7: Relationship Mapping ===")
            phase7_result = await self.phase7_agent.execute_phase()
            self.logger.info(f"Phase 7 result: {phase7_result}")
            
            # Phase 8: RIG Assembly
            self.logger.info("=== PHASE 8: RIG Assembly ===")
            phase8_result = await self.phase8_agent.execute_phase()
            self.logger.info(f"Phase 8 result: {phase8_result}")
            
            # Log final RIG state
            self.logger.info("SUCCESS: V5 RIG generation completed!")
            self.logger.info(f"Final RIG state: {self.rig}")
            
            # Log RIG summary
            components_count = len(self.rig.components) if self.rig.components else 0
            tests_count = len(self.rig.tests) if self.rig.tests else 0
            aggregators_count = len(self.rig.aggregators) if self.rig.aggregators else 0
            runners_count = len(self.rig.runners) if self.rig.runners else 0
            utilities_count = len(self.rig.utilities) if self.rig.utilities else 0
            
            self.logger.info(f"RIG Summary: {components_count} components, {tests_count} tests, {aggregators_count} aggregators, {runners_count} runners, {utilities_count} utilities")
            
            return self.rig
            
        except Exception as e:
            self.logger.error(f"V5 RIG generation failed: {e}")
            raise
    
    def get_rig_summary(self) -> dict:
        """Get a summary of the current RIG state."""
        return {
            "components_count": len(self.rig.components) if self.rig.components else 0,
            "tests_count": len(self.rig.tests) if self.rig.tests else 0,
            "aggregators_count": len(self.rig.aggregators) if self.rig.aggregators else 0,
            "runners_count": len(self.rig.runners) if self.rig.runners else 0,
            "utilities_count": len(self.rig.utilities) if self.rig.utilities else 0,
            "repository_name": self.rig.repository.name if self.rig.repository else "Unknown",
            "build_system": self.rig.build_system.name if self.rig.build_system else "Unknown"
        }
