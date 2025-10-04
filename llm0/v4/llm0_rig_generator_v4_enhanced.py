#!/usr/bin/env python3
"""
Enhanced V4+ RIG Generator with Phase 8 Enhancement

This generator uses the original V4 architecture for phases 1-7 and the enhanced
Phase 8 with direct RIG manipulation tools to avoid context explosion.
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from core.rig import RIG
from .phase1_repository_overview_agent_v4 import RepositoryOverviewAgentV4
from .phase2_source_structure_agent_v4 import SourceStructureDiscoveryAgentV4
from .phase3_test_structure_agent_v4 import TestStructureDiscoveryAgentV4
from .phase4_build_system_agent_v4 import BuildSystemAnalysisAgentV4
from .phase5_artifact_discovery_agent_v4 import ArtifactDiscoveryAgentV4
from .phase6_component_classification_agent_v4 import ComponentClassificationAgentV4
from .phase7_relationship_mapping_agent_v4 import RelationshipMappingAgentV4
from .phase8_rig_assembly_agent_v4_enhanced import RIGAssemblyAgentV4Enhanced


class LLMRIGGeneratorV4Enhanced:
    """Enhanced V4+ RIG Generator with Phase 8 enhancement."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path
        self.logger = logging.getLogger("LLMRIGGeneratorV4Enhanced")
        self.logger.setLevel(logging.INFO)
        
        # Create a single RIG instance that will grow through all phases
        self.rig = RIG()
        
        # Initialize agents for phases 1-7 (unchanged V4 architecture)
        self.phase1_agent = RepositoryOverviewAgentV4(repository_path)
        self.phase2_agent = SourceStructureDiscoveryAgentV4(repository_path)
        self.phase3_agent = TestStructureDiscoveryAgentV4(repository_path)
        self.phase4_agent = BuildSystemAnalysisAgentV4(repository_path)
        self.phase5_agent = ArtifactDiscoveryAgentV4(repository_path)
        self.phase6_agent = ComponentClassificationAgentV4(repository_path)
        self.phase7_agent = RelationshipMappingAgentV4(repository_path)
        
        # Enhanced Phase 8 agent with RIG manipulation tools
        self.phase8_agent = RIGAssemblyAgentV4Enhanced(repository_path, self.rig)
        
        self.logger.info(f"Initialized Enhanced V4+ RIG Generator for: {repository_path}")
        self.logger.info(f"Initial RIG state: {self.rig}")
    
    async def generate_rig(self) -> RIG:
        """Generate RIG using enhanced V4+ architecture."""
        self.logger.info("Generating RIG using Enhanced V4+ architecture...")
        self.logger.info("RUNNING: Enhanced V4+ RIG Generation (Phases 1-7: V4, Phase 8: Enhanced)...")
        
        try:
            # Phase 1: Repository Overview (V4)
            self.logger.info("=== PHASE 1: Repository Overview (V4) ===")
            phase1_result = await self.phase1_agent.execute_phase()
            self.logger.info(f"Phase 1 result: {phase1_result}")
            
            # Phase 2: Source Structure Discovery (V4)
            self.logger.info("=== PHASE 2: Source Structure Discovery (V4) ===")
            phase2_result = await self.phase2_agent.execute_phase(phase1_result)
            self.logger.info(f"Phase 2 result: {phase2_result}")
            
            # Phase 3: Test Structure Discovery (V4)
            self.logger.info("=== PHASE 3: Test Structure Discovery (V4) ===")
            phase3_result = await self.phase3_agent.execute_phase(phase1_result, phase2_result)
            self.logger.info(f"Phase 3 result: {phase3_result}")
            
            # Phase 4: Build System Analysis (V4)
            self.logger.info("=== PHASE 4: Build System Analysis (V4) ===")
            phase4_result = await self.phase4_agent.execute_phase(phase1_result, phase2_result, phase3_result)
            self.logger.info(f"Phase 4 result: {phase4_result}")
            
            # Phase 5: Artifact Discovery (V4)
            self.logger.info("=== PHASE 5: Artifact Discovery (V4) ===")
            phase5_result = await self.phase5_agent.execute_phase(phase1_result, phase2_result, phase3_result, phase4_result)
            self.logger.info(f"Phase 5 result: {phase5_result}")
            
            # Phase 6: Component Classification (V4)
            self.logger.info("=== PHASE 6: Component Classification (V4) ===")
            phase6_result = await self.phase6_agent.execute_phase(phase1_result, phase2_result, phase3_result, phase4_result, phase5_result)
            self.logger.info(f"Phase 6 result: {phase6_result}")
            
            # Phase 7: Relationship Mapping (V4)
            self.logger.info("=== PHASE 7: Relationship Mapping (V4) ===")
            phase7_result = await self.phase7_agent.execute_phase(phase1_result, phase2_result, phase3_result, phase4_result, phase5_result, phase6_result)
            self.logger.info(f"Phase 7 result: {phase7_result}")
            
            # Phase 8: Enhanced RIG Assembly (V4+)
            self.logger.info("=== PHASE 8: Enhanced RIG Assembly (V4+) ===")
            
            # Collect all phase results for Phase 8
            phase_results = {
                "phase1": phase1_result,
                "phase2": phase2_result,
                "phase3": phase3_result,
                "phase4": phase4_result,
                "phase5": phase5_result,
                "phase6": phase6_result,
                "phase7": phase7_result
            }
            
            # Execute enhanced Phase 8 with RIG manipulation tools
            phase8_result = await self.phase8_agent.execute_phase(phase_results)
            self.logger.info(f"Phase 8 result: {phase8_result}")
            
            # Log final RIG state
            self.logger.info("SUCCESS: Enhanced V4+ RIG generation completed!")
            self.logger.info(f"Final RIG state: {self.rig}")
            
            # Log RIG summary
            components_count = len(self.rig.components) if self.rig.components else 0
            tests_count = len(self.rig.tests) if self.rig.tests else 0
            
            self.logger.info(f"RIG Summary: {components_count} components, {tests_count} tests")
            
            return self.rig
            
        except Exception as e:
            self.logger.error(f"Enhanced V4+ RIG generation failed: {e}")
            raise
    
    def get_rig_summary(self) -> dict:
        """Get a summary of the current RIG state."""
        return {
            "components_count": len(self.rig.components) if self.rig.components else 0,
            "tests_count": len(self.rig.tests) if self.rig.tests else 0,
            "repository_name": self.rig.repository.name if self.rig.repository else "Unknown",
            "build_system": self.rig.build_system.name if self.rig.build_system else "Unknown"
        }
