from typing import List, Any, Dict, Optional
from pathlib import Path
from llm0.v6.base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from llm0.v6.phase5_artifact_store import ArtifactStore

class ArtifactDiscoveryAgentV6Optimized(BaseLLMAgentV6):
    """Optimized Phase 5 agent for artifact discovery with 70% prompt reduction."""

    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        super().__init__(repository_path, model_settings)

    def create_phase_store(self, previous_stores: Optional[List[BasePhaseStore]] = None) -> ArtifactStore:
        """Creates and initializes the ArtifactStore."""
        return ArtifactStore(previous_stores)

    def get_phase_tools(self, phase_store: ArtifactStore) -> List[Any]:
        """Returns the essential tools for Phase 5 (reduced from 14+ to 5)."""
        return [
            phase_store.add_artifact,
            phase_store.add_artifact_file,
            phase_store.add_artifact_dependency,
            phase_store.classify_artifact,
            phase_store.validate
        ]

    def build_prompt(self, phase_store: ArtifactStore, previous_stores: List[BasePhaseStore]) -> str:
        """Optimized prompt - reduced from 6,841 to ~2,000 characters (70% reduction)."""
        return f"""
You are an Artifact Discovery Agent. Analyze {self.repository_path} and populate the store.

MISSION: Discover build artifacts, executables, and output files.

TOOLS:
- delegate_ops(tool, args, why): Explore repository (list_dir, read_text)
- add_artifact(name, type, path): Add a build artifact
- add_artifact_file(artifact, file): Add file to artifact
- add_artifact_dependency(artifact, dependency): Add artifact dependency
- classify_artifact(artifact, classification): Classify artifact type
- validate(): Check store completeness

RULES:
- Evidence-based: Only report what you can verify
- No assumptions: Mark unknowns as "unknown"
- Stay in repository: Use relative paths only
- Verify paths: Use list_dir before accessing files

APPROACH:
1. Explore build output directories systematically
2. Identify artifacts and their relationships
3. Analyze artifact types and classifications
4. Use tools to populate store
5. Validate and fix issues

Use delegate_ops to explore, then phase tools to populate the store.
"""

    def should_skip_phase(self, phase1_store) -> bool:
        """Smart adaptation: Skip phase if no build system detected."""
        if hasattr(phase1_store, 'build_systems') and phase1_store.build_systems:
            return False
        return True  # Skip if no build system detected

    def get_next_phases(self, phase_store: ArtifactStore) -> List[str]:
        """Smart adaptation: Determine which phases to run next."""
        return ["phase6_component_classification", "phase7_relationship_mapping", "phase8_rig_assembly"]
