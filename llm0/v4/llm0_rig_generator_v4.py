#!/usr/bin/env python3
"""
LLM-based RIG Generator V4 - 8-Phase Architecture
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add agentkit-gf to path
agentkit_gf_path = Path("C:/src/github.com/GreenFuze/agentkit-gf")
sys.path.insert(0, str(agentkit_gf_path))

# Import all phase agents
from .phase1_repository_overview_agent_v4 import RepositoryOverviewAgentV4
from .phase2_source_structure_agent_v4 import SourceStructureDiscoveryAgentV4
from .phase3_test_structure_agent_v4 import TestStructureDiscoveryAgentV4
from .phase4_build_system_agent_v4 import BuildSystemAnalysisAgentV4
from .phase5_artifact_discovery_agent_v4 import ArtifactDiscoveryAgentV4
from .phase6_component_classification_agent_v4 import ComponentClassificationAgentV4
from .phase7_relationship_mapping_agent_v4 import RelationshipMappingAgentV4
from .phase8_rig_assembly_agent_v4 import RIGAssemblyAgentV4

# Import core RIG classes
from core.rig import RIG
from core.schemas import RepositoryInfo, BuildSystemInfo


class LLMRIGGeneratorV4:
    """V4 LLM RIG Generator with 8-phase architecture."""
    
    def __init__(self, repository_path: Path):
        self.repository_path = repository_path.absolute()
        self.logger = logging.getLogger("LLMRIGGeneratorV4")
        self.logger.setLevel(logging.INFO)
        
        # Initialize all phase agents
        self.phase1_agent = RepositoryOverviewAgentV4(repository_path)
        self.phase2_agent = SourceStructureDiscoveryAgentV4(repository_path)
        self.phase3_agent = TestStructureDiscoveryAgentV4(repository_path)
        self.phase4_agent = BuildSystemAnalysisAgentV4(repository_path)
        self.phase5_agent = ArtifactDiscoveryAgentV4(repository_path)
        self.phase6_agent = ComponentClassificationAgentV4(repository_path)
        self.phase7_agent = RelationshipMappingAgentV4(repository_path)
        self.phase8_agent = RIGAssemblyAgentV4(repository_path)
    
    async def generate_rig(self) -> RIG:
        """Generate RIG using all 8 phases."""
        self.logger.info("RUNNING: Complete RIG Generation (V4 8-Phase Architecture)...")
        
        try:
            # Phase 1: Repository Overview
            self.logger.info("=== PHASE 1: Repository Overview ===")
            repository_overview = await self.phase1_agent.execute_phase()
            
            # Phase 2: Source Structure Discovery
            self.logger.info("=== PHASE 2: Source Structure Discovery ===")
            source_structure = await self.phase2_agent.execute_phase(repository_overview)
            
            # Phase 3: Test Structure Discovery
            self.logger.info("=== PHASE 3: Test Structure Discovery ===")
            test_structure = await self.phase3_agent.execute_phase(repository_overview, source_structure)
            
            # Phase 4: Build System Analysis
            self.logger.info("=== PHASE 4: Build System Analysis ===")
            build_analysis = await self.phase4_agent.execute_phase(repository_overview, source_structure, test_structure)
            
            # Phase 5: Artifact Discovery
            self.logger.info("=== PHASE 5: Artifact Discovery ===")
            artifact_analysis = await self.phase5_agent.execute_phase(repository_overview, source_structure, test_structure, build_analysis)
            
            # Phase 6: Component Classification
            self.logger.info("=== PHASE 6: Component Classification ===")
            classified_components = await self.phase6_agent.execute_phase(repository_overview, source_structure, test_structure, build_analysis, artifact_analysis)
            
            # Phase 7: Relationship Mapping
            self.logger.info("=== PHASE 7: Relationship Mapping ===")
            relationships = await self.phase7_agent.execute_phase(repository_overview, source_structure, test_structure, build_analysis, artifact_analysis, classified_components)
            
            # Phase 8: RIG Assembly
            self.logger.info("=== PHASE 8: RIG Assembly ===")
            rig_assembly = await self.phase8_agent.execute_phase(repository_overview, source_structure, test_structure, build_analysis, artifact_analysis, classified_components, relationships)
            
            # Convert assembly results to RIG object
            rig = self._convert_to_rig(rig_assembly)
            
            self.logger.info("SUCCESS: Complete RIG generation completed!")
            return rig
            
        except Exception as e:
            self.logger.error(f"RIG generation failed: {e}")
            raise
    
    def _convert_to_rig(self, rig_assembly: Dict[str, Any]) -> RIG:
        """Convert assembly results to RIG object."""
        try:
            rig = RIG()
            
            # Set repository info
            if "repository_info" in rig_assembly:
                repo_info = rig_assembly["repository_info"]
                rig.repository = RepositoryInfo(
                    name=repo_info.get("name", "Unknown"),
                    root_path=Path(repo_info.get("root_path", str(self.repository_path))),
                    build_directory=Path(repo_info.get("build_directory", "build")),
                    output_directory=Path(repo_info.get("output_directory", "output")),
                    configure_command=repo_info.get("configure_command", ""),
                    build_command=repo_info.get("build_command", ""),
                    install_command=repo_info.get("install_command", ""),
                    test_command=repo_info.get("test_command", "")
                )
            
            # Set build system info
            if "build_system_info" in rig_assembly:
                build_info = rig_assembly["build_system_info"]
                rig.build_system = BuildSystemInfo(
                    name=build_info.get("name", "Unknown"),
                    version=build_info.get("version", "Unknown"),
                    build_type=build_info.get("build_type", "Unknown")
                )
            
            return rig
            
        except Exception as e:
            self.logger.error(f"Failed to convert to RIG: {e}")
            # Return basic RIG if conversion fails
            rig = RIG()
            rig.repository = RepositoryInfo(
                name="Unknown",
                root_path=self.repository_path,
                build_directory=self.repository_path / "build",
                output_directory=self.repository_path / "output",
                configure_command="",
                build_command="",
                install_command="",
                test_command=""
            )
            rig.build_system = BuildSystemInfo(
                name="Unknown",
                version="Unknown",
                build_type="Unknown"
            )
            return rig
