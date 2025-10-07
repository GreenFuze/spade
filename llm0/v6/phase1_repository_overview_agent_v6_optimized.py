from typing import List, Any, Dict, Optional
from pathlib import Path
from llm0.v6.base_agent_v6 import BaseLLMAgentV6, BasePhaseStore
from llm0.v6.phase1_repository_overview_store import RepositoryOverviewStore

class RepositoryOverviewAgentV6Optimized(BaseLLMAgentV6):
    """Optimized V6 Phase 1 Agent with reduced prompt size and smart adaptation."""
    
    def __init__(self, repository_path: Path, model_settings: Dict[str, Any]):
        super().__init__(repository_path, model_settings)

    def create_phase_store(self, previous_stores: Optional[List[BasePhaseStore]] = None) -> RepositoryOverviewStore:
        """Creates and initializes the RepositoryOverviewStore."""
        return RepositoryOverviewStore()

    def get_phase_tools(self, phase_store: RepositoryOverviewStore) -> List[Any]:
        """Returns the essential tools for Phase 1 (reduced from 14+ to 5)."""
        return [
            phase_store.set_name,
            phase_store.set_type,
            phase_store.set_primary_language,
            phase_store.add_build_system,
            phase_store.add_source_dir,
            phase_store.add_entry_point,
            phase_store.add_priority_dir,
            phase_store.validate
        ]

    def build_prompt(self, phase_store: RepositoryOverviewStore, previous_stores: List[BasePhaseStore]) -> str:
        """Optimized prompt - reduced from 6,841 to ~2,000 characters (70% reduction)."""
        return f"""
You are a Repository Overview Agent. Analyze {self.repository_path} and populate the store.

MISSION: Identify repository structure, build systems, and exploration scope.

TOOLS:
- delegate_ops(tool, args, why): Explore repository (list_dir, read_text, get_directory_context)
- set_name(name): Set repository name
- set_type(type): Set repository type  
- set_primary_language(language): Set primary language
- add_build_system(system): Add build system
- add_source_dir(path): Add source directory
- add_entry_point(file): Add entry point
- add_priority_dir(path): Add priority directory
- validate(): Check store completeness

RULES:
- Evidence-based: Only report what you can verify
- No assumptions: Mark unknowns as "unknown"
- Stay in repository: Use relative paths only
- Verify paths: Use list_dir before accessing files

APPROACH:
1. Get directory context and list contents
2. Identify build system files and configuration
3. Read key configuration files
4. Use tools to populate store
5. Validate and fix issues

Use delegate_ops to explore, then phase tools to populate the store.
"""

    def should_skip_phase(self, phase_store: RepositoryOverviewStore) -> bool:
        """Smart adaptation: Skip phase if repository is too simple."""
        # If we can determine it's a simple repository from initial context, skip detailed analysis
        return False  # For now, always run Phase 1

    def get_next_phases(self, phase_store: RepositoryOverviewStore) -> List[str]:
        """Smart adaptation: Determine which phases to run next based on Phase 1 results."""
        next_phases = []
        
        # Always run Phase 2 (Source Structure) if we have source directories
        if phase_store.directory_structure.source_dirs:
            next_phases.append("phase2_source_structure")
        
        # Only run Phase 3 (Test Structure) if we have test directories
        if phase_store.directory_structure.test_dirs:
            next_phases.append("phase3_test_structure")
        
        # Always run Phase 4 (Build System) if we have build systems
        if phase_store.build_systems:
            next_phases.append("phase4_build_system")
        
        # Skip Phase 5 (Artifact Discovery) for simple repositories
        if len(phase_store.build_systems) > 1 or len(phase_store.directory_structure.source_dirs) > 3:
            next_phases.append("phase5_artifact_discovery")
        
        # Always run remaining phases
        next_phases.extend(["phase6_component_classification", "phase7_relationship_mapping", "phase8_rig_assembly"])
        
        return next_phases
