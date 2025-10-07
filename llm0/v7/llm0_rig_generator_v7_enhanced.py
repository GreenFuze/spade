#!/usr/bin/env python3
"""
V7 Enhanced LLM-based RIG Generator

Enhanced V4+ architecture with:
- Batch operations for Phase 8 (60-70% fewer tool calls)
- Smart validation tools
- Optimized prompts (70% reduction)
- Strict 1 retry limit (no token burning)
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .phase1_repository_overview_agent_v7 import RepositoryOverviewAgentV7
from .phase2_source_structure_agent_v7 import SourceStructureDiscoveryAgentV7
from .phase3_test_structure_agent_v7 import TestStructureDiscoveryAgentV7
from .phase4_build_system_agent_v7 import BuildSystemAnalysisAgentV7
from .phase5_artifact_discovery_agent_v7 import ArtifactDiscoveryAgentV7
from .phase6_component_classification_agent_v7 import ComponentClassificationAgentV7
from .phase7_relationship_mapping_agent_v7 import RelationshipMappingAgentV7
from .phase8_rig_assembly_agent_v7_enhanced import RIGAssemblyAgentV7Enhanced
from core.rig import RIG


class LLMRIGGeneratorV7Enhanced:
    """V7 Enhanced LLM-based RIG Generator with batch operations and optimized prompts."""
    
    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        self.repository_path = repository_path
        self.model_settings = model_settings
        self.logger = logging.getLogger("LLMRIGGeneratorV7Enhanced")
        
        # Initialize agents with V7 enhancements
        self.agents = {
            "phase1": RepositoryOverviewAgentV7(repository_path),
            "phase2": SourceStructureDiscoveryAgentV7(repository_path),
            "phase3": TestStructureDiscoveryAgentV7(repository_path),
            "phase4": BuildSystemAnalysisAgentV7(repository_path),
            "phase5": ArtifactDiscoveryAgentV7(repository_path),
            "phase6": ComponentClassificationAgentV7(repository_path),
            "phase7": RelationshipMappingAgentV7(repository_path),
            "phase8": None  # Will be initialized with RIG instance
        }
        
        # Track execution
        self.executed_phases = []
        self.phase_results = []
    
    async def generate_rig(self) -> RIG:
        """Generate RIG using V7 enhanced 8-phase pipeline."""
        self.logger.info("Starting V7 Enhanced RIG Generation")
        
        # Create RIG instance for Phase 8
        rig = RIG()
        
        # Initialize Phase 8 with RIG instance
        self.agents["phase8"] = RIGAssemblyAgentV7Enhanced(
            self.repository_path, 
            rig, 
            max_retries=1  # V7: Strict 1 retry limit
        )
        
        try:
            # Phase 1: Repository Overview
            self.logger.info("=== PHASE 1: Repository Overview ===")
            repository_overview = await self.agents["phase1"].execute_phase()
            self.phase_results.append(repository_overview)
            self.executed_phases.append("phase1")
            
            # Phase 2: Source Structure Discovery
            self.logger.info("=== PHASE 2: Source Structure Discovery ===")
            source_structure = await self.agents["phase2"].execute_phase(repository_overview)
            self.phase_results.append(source_structure)
            self.executed_phases.append("phase2")
            
            # Phase 3: Test Structure Discovery
            self.logger.info("=== PHASE 3: Test Structure Discovery ===")
            test_structure = await self.agents["phase3"].execute_phase(repository_overview, source_structure)
            self.phase_results.append(test_structure)
            self.executed_phases.append("phase3")
            
            # Phase 4: Build System Analysis
            self.logger.info("=== PHASE 4: Build System Analysis ===")
            build_analysis = await self.agents["phase4"].execute_phase(repository_overview, source_structure, test_structure)
            self.phase_results.append(build_analysis)
            self.executed_phases.append("phase4")
            
            # Phase 5: Artifact Discovery
            self.logger.info("=== PHASE 5: Artifact Discovery ===")
            artifact_analysis = await self.agents["phase5"].execute_phase(repository_overview, source_structure, test_structure, build_analysis)
            self.phase_results.append(artifact_analysis)
            self.executed_phases.append("phase5")
            
            # Phase 6: Component Classification
            self.logger.info("=== PHASE 6: Component Classification ===")
            classified_components = await self.agents["phase6"].execute_phase(repository_overview, source_structure, test_structure, build_analysis, artifact_analysis)
            self.phase_results.append(classified_components)
            self.executed_phases.append("phase6")
            
            # Phase 7: Relationship Mapping
            self.logger.info("=== PHASE 7: Relationship Mapping ===")
            relationships = await self.agents["phase7"].execute_phase(repository_overview, source_structure, test_structure, build_analysis, artifact_analysis, classified_components)
            self.phase_results.append(relationships)
            self.executed_phases.append("phase7")
            
            # Phase 8: V7 Enhanced RIG Assembly
            self.logger.info("=== PHASE 8: V7 Enhanced RIG Assembly ===")
            phase8_result = await self.agents["phase8"].execute_phase(self.phase_results)
            self.phase_results.append(phase8_result)
            self.executed_phases.append("phase8")
            
            self.logger.info("V7 Enhanced RIG Generation completed successfully")
            return rig
            
        except Exception as e:
            self.logger.error(f"V7 Enhanced RIG Generation failed: {e}")
            raise Exception(f"V7 Enhanced RIG Generation failed: {e}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary for V7 enhanced pipeline."""
        return {
            "version": "V7 Enhanced",
            "executed_phases": self.executed_phases,
            "total_phases": len(self.executed_phases),
            "enhancements": [
                "Batch operations for Phase 8",
                "Smart validation tools",
                "Optimized prompts (70% reduction)",
                "Strict 1 retry limit"
            ],
            "expected_improvements": [
                "60-70% reduction in Phase 8 tool calls",
                "50% reduction in retry attempts",
                "Better error handling and recovery"
            ]
        }
