import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from llm0.v6.base_agent_v6 import BasePhaseStore
from llm0.v6.phase1_repository_overview_agent_v6_optimized import RepositoryOverviewAgentV6Optimized
from llm0.v6.phase2_source_structure_agent_v6_optimized import SourceStructureDiscoveryAgentV6Optimized
from llm0.v6.phase3_test_structure_agent_v6_optimized import TestStructureDiscoveryAgentV6Optimized
from llm0.v6.phase4_build_system_agent_v6_optimized import BuildSystemAnalysisAgentV6Optimized
from llm0.v6.phase5_artifact_discovery_agent_v6_optimized import ArtifactDiscoveryAgentV6Optimized
from llm0.v6.phase6_component_classification_agent_v6_optimized import ComponentClassificationAgentV6Optimized
from llm0.v6.phase7_relationship_mapping_agent_v6_optimized import RelationshipMappingAgentV6Optimized
from llm0.v6.phase8_rig_assembly_agent_v6_optimized import RIGAssemblyAgentV6Optimized
# Import other optimized agents as they are created

logger = logging.getLogger(__name__)

class LLMRIGGeneratorV6Smart:
    """Smart V6 RIG Generator with adaptive phase selection and optimized prompts."""

    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        self.repository_path = repository_path
        self.model_settings = model_settings
        self.phase_results: List[BasePhaseStore] = []
        self.executed_phases: List[str] = []
        
        # Initialize all possible phase agents
        self.phase_agents = {
            "phase1_repository_overview": RepositoryOverviewAgentV6Optimized(repository_path, model_settings),
            "phase2_source_structure": SourceStructureDiscoveryAgentV6Optimized(repository_path, model_settings),
            "phase3_test_structure": TestStructureDiscoveryAgentV6Optimized(repository_path, model_settings),
            "phase4_build_system": BuildSystemAnalysisAgentV6Optimized(repository_path, model_settings),
            "phase5_artifact_discovery": ArtifactDiscoveryAgentV6Optimized(repository_path, model_settings),
            "phase6_component_classification": ComponentClassificationAgentV6Optimized(repository_path, model_settings),
            "phase7_relationship_mapping": RelationshipMappingAgentV6Optimized(repository_path, model_settings),
            "phase8_rig_assembly": RIGAssemblyAgentV6Optimized(repository_path, model_settings),
        }

    async def generate_rig(self) -> List[BasePhaseStore]:
        """Smart RIG generation with adaptive phase selection."""
        logger.info(f"Starting Smart V6 RIG generation for {self.repository_path}")

        # Phase 1: Always start with repository overview
        phase1_agent = self.phase_agents["phase1_repository_overview"]
        phase1_result = await phase1_agent.execute_phase([])
        self.phase_results.append(phase1_result)
        self.executed_phases.append("phase1_repository_overview")
        
        logger.info(f"Phase 1 completed. Result summary: {phase1_result.get_summary()}")

        # Smart phase selection based on Phase 1 results
        next_phases = phase1_agent.get_next_phases(phase1_result)
        logger.info(f"Smart phase selection: {next_phases}")

        # Execute selected phases
        for phase_name in next_phases:
            if phase_name in self.phase_agents:
                logger.info(f"Executing {phase_name}")
                phase_agent = self.phase_agents[phase_name]
                
                # Check if we should skip this phase
                if hasattr(phase_agent, 'should_skip_phase'):
                    if phase_agent.should_skip_phase(phase1_result):
                        logger.info(f"Skipping {phase_name} - not needed for this repository")
                        continue
                
                # Execute phase with previous results
                phase_result = await phase_agent.execute_phase(self.phase_results)
                self.phase_results.append(phase_result)
                self.executed_phases.append(phase_name)
                
                logger.info(f"{phase_name} completed. Result summary: {phase_result.get_summary()}")
            else:
                logger.warning(f"Phase {phase_name} not implemented yet, skipping")

        logger.info(f"Finished Smart V6 RIG generation. Executed phases: {self.executed_phases}")
        return self.phase_results

    def get_rig_summary(self) -> Dict[str, Any]:
        """Get summary of the generated RIG."""
        if not self.phase_results:
            return {"status": "No phases executed"}
        
        return {
            "executed_phases": self.executed_phases,
            "total_phases": len(self.phase_results),
            "final_result": self.phase_results[-1].get_summary() if self.phase_results else None
        }

    def get_adaptation_info(self) -> Dict[str, Any]:
        """Get information about the smart adaptation decisions made."""
        return {
            "repository_path": str(self.repository_path),
            "executed_phases": self.executed_phases,
            "total_phases_available": len(self.phase_agents),
            "adaptation_ratio": len(self.executed_phases) / len(self.phase_agents),
            "smart_selection": True
        }
