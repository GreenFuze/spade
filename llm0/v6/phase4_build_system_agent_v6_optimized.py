from typing import List, Any, Dict, Optional
from pathlib import Path
from llm0.v6.base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from llm0.v6.phase4_build_system_store import BuildSystemStore

class BuildSystemAnalysisAgentV6Optimized(BaseLLMAgentV6):
    """Optimized Phase 4 agent for build system analysis with 70% prompt reduction."""

    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        super().__init__(repository_path, model_settings)

    def create_phase_store(self, previous_stores: Optional[List[BasePhaseStore]] = None) -> BuildSystemStore:
        """Creates and initializes the BuildSystemStore."""
        return BuildSystemStore(previous_stores)

    def get_phase_tools(self, phase_store: BuildSystemStore) -> List[Any]:
        """Returns the essential tools for Phase 4 (reduced from 14+ to 5)."""
        return [
            phase_store.add_build_target,
            phase_store.add_build_dependency,
            phase_store.add_build_configuration,
            phase_store.add_build_artifact,
            phase_store.validate
        ]

    def build_prompt(self, phase_store: BuildSystemStore, previous_stores: List[BasePhaseStore]) -> str:
        """Optimized prompt - reduced from 6,841 to ~2,000 characters (70% reduction)."""
        return f"""
You are a Build System Analysis Agent. Analyze {self.repository_path} and populate the store.

MISSION: Discover build targets, dependencies, and configuration.

TOOLS:
- delegate_ops(tool, args, why): Explore repository (list_dir, read_text)
- add_build_target(name, type, path): Add a build target
- add_build_dependency(target, dependency): Add dependency
- add_compiler_config(language, config): Add compiler configuration
- add_build_artifact(target, artifact): Add build artifact
- validate(): Check store completeness

RULES:
- Evidence-based: Only report what you can verify
- No assumptions: Mark unknowns as "unknown"
- Stay in repository: Use relative paths only
- Verify paths: Use list_dir before accessing files

APPROACH:
1. Explore build configuration files systematically
2. Identify build targets and their relationships
3. Analyze compiler settings and dependencies
4. Use tools to populate store
5. Validate and fix issues

Use delegate_ops to explore, then phase tools to populate the store.
"""

    def should_skip_phase(self, phase1_store) -> bool:
        """Smart adaptation: Skip phase if no build system detected."""
        if hasattr(phase1_store, 'build_systems') and phase1_store.build_systems:
            return False
        return True  # Skip if no build system detected

    def get_next_phases(self, phase_store: BuildSystemStore) -> List[str]:
        """Smart adaptation: Determine which phases to run next."""
        return ["phase5_artifact_discovery", "phase6_component_classification", 
                "phase7_relationship_mapping", "phase8_rig_assembly"]
